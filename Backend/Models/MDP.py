"""
Simplified GPU-accelerated Markov Decision Process for golf hole simulation.
Uses PyTorch for GPU computation of value iteration.
"""

import numpy as np
import torch
import json
from pathlib import Path
import sys

try:
    from tqdm.auto import tqdm
except ImportError:
    tqdm = None

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Models.GaussianMixture import GaussianMixtureModel
from Simulation.golfhole import Hole
from Simulation.HoleSetUp.hole_simple import create_hole


BASE_DIR = Path(__file__).resolve().parent.parent
MDP_DIR = BASE_DIR / "Persistence" / "MDP"


class GolfHoleMDP:
    """
    GPU-accelerated MDP for simplified golf hole.
    
    Goal: Get within 20 yards of pin
    Penalty: -1 per stroke
    Out of bounds: Return to original position, -1 stroke
    """
    
    def __init__(self, hole = None, club_ids = [], grid_step=10, device=None):
        """
        Args:
            hole: Hole object with pin_location, tee_location, x (width), y (depth)
            club_ids: List of club IDs
            grid_step: Discretization grid size in yards
            device: PyTorch device ('cuda', 'cpu', or None for auto)
        """
        if hole is None:
            hole = create_hole()

        self.hole = hole
        self.club_ids = club_ids
        self.num_clubs = len(club_ids)
        self.clubs = self.setup_clubs(club_ids)
        self.grid_step = grid_step
        
        self.pin_location = np.array(hole.pin_location, dtype=np.float32)
        self.tee_location = np.array(hole.tee_location, dtype=np.float32)
        
        self.x_min = -hole.x / 2
        self.x_max = hole.x / 2
        self.y_min = 0
        self.y_max = hole.y
        
        self.terminal_radius = 20.0
        
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"Using device: {self.device}")
        
        state_grid_x = np.arange(self.x_min, self.x_max + 1e-9, self.grid_step)
        state_grid_y = np.arange(self.y_min, self.y_max + 1e-9, self.grid_step)
        
        self.grid_x = state_grid_x
        self.grid_y = state_grid_y
        
        states_list = [(float(x), float(y)) for x in state_grid_x for y in state_grid_y]
        self.states = states_list
        self.num_states = len(states_list)
        
        self.state_to_idx = {state: i for i, state in enumerate(states_list)}
        
        self.states_tensor = torch.tensor(
            [[s[0], s[1]] for s in states_list], 
            dtype=torch.float32, 
            device=self.device
        )
        self.pin_tensor = torch.tensor(self.pin_location, dtype=torch.float32, device=self.device)

        self.value_function = None
        self.policy = None
        
        print(f"Initialized MDP: {self.num_states} states, {self.num_clubs} clubs")

    def setup_clubs(self, club_ids):
        clubs = []
        print(f"Loading club models: {club_ids}")
        for club_id in club_ids:
            try:
                club = GaussianMixtureModel()
                club.load(club_id)
                clubs.append(club)
            except FileNotFoundError:
                raise FileNotFoundError(f"Club model not found for id: {club_id}")
        return clubs

    def get_club_ids(self):
        return self.club_ids
    
    def _snap_to_grid(self, x, y):
        gx = round((x - self.x_min) / self.grid_step) * self.grid_step + self.x_min
        gy = round((y - self.y_min) / self.grid_step) * self.grid_step + self.y_min
        return (float(gx), float(gy))
    
    def _is_out_of_bounds(self, x, y):
        return x < self.x_min or x > self.x_max or y < self.y_min or y > self.y_max
    
    def is_terminal(self, state):
        """Check if state is within terminal radius of pin."""
        dist = np.linalg.norm(np.array(state) - self.pin_location)
        return dist <= self.terminal_radius
    
    def get_actions(self, state):
        """
        Generate actions for a state.
        Returns list of (club_idx, target_x, target_y) tuples.
        """
        x, y = state

        if self.is_terminal(state):
            return []
        
        actions = []
        
        to_pin = self.pin_location - np.array([x, y])
        dist_to_pin = np.linalg.norm(to_pin)
        
        if dist_to_pin < 1e-6:
            return []
        
        pin_dir = to_pin / dist_to_pin
        pin_angle = np.arctan2(pin_dir[1], pin_dir[0])
        
        for club_idx in range(self.num_clubs):
            actions.append((club_idx, self.pin_location[0], self.pin_location[1]))
            
            angle_spread = np.pi / 12
            for offset in np.linspace(-angle_spread, angle_spread, 12):
                angle = pin_angle + offset
                aim_dist = min(dist_to_pin * 1.5, 200)
                
                target_x = x + aim_dist * np.cos(angle)
                target_y = y + aim_dist * np.sin(angle)
                
                actions.append((club_idx, float(target_x), float(target_y)))
        
        return actions
    
   
    def simulate_shot(self, state, action, num_samples=100):
        """
        Simulate a shot and return next state distribution.
        """
        x_start, y_start = state
        club_idx, target_x, target_y = action
        
        club = self.clubs[club_idx]
        
        target_vec = np.array([target_x - x_start, target_y - y_start])
        target_dist = np.linalg.norm(target_vec)
        
        if target_dist < 1e-6:
            target_dir = np.array([0, 1])
        else:
            target_dir = target_vec / target_dist
        
        # Sample from GMM (returns tuple of (samples, labels))
        samples, _ = club.sample(n_samples=num_samples)
        
        # Transform samples to world coordinates
        # GMM samples are [lateral_offset, distance] in club's coordinate system
        perp_dir = np.array([-target_dir[1], target_dir[0]])
        
        # Extract lateral and distance components
        laterals = samples[:, 0][:, np.newaxis]
        distances = samples[:, 1][:, np.newaxis]
        
        # Compute landing positions
        start_pos = np.array([x_start, y_start])
        offsets = distances * target_dir + laterals * perp_dir
        
        landings = start_pos + offsets
        
        next_states = {}
        total_reward = 0
        
        for landing in landings:
            x_end, y_end = landing
            reward = -1
            
            if self._is_out_of_bounds(x_end, y_end):
                next_state = (x_start, y_start)
            elif np.linalg.norm(landing - self.pin_location) <= self.terminal_radius:
                next_state = tuple(self.pin_location)
            else:
                next_state = self._snap_to_grid(x_end, y_end)
            
            total_reward += reward
            next_states[next_state] = next_states.get(next_state, 0) + 1
        
        next_state_dist = {s: count / num_samples for s, count in next_states.items()}
        expected_reward = total_reward / num_samples
        
        return expected_reward, next_state_dist
    
    def build_transition_matrices(self, num_samples=100, show_progress=True):
        """
        Build sparse transition matrices for all state-action pairs.
        Returns tensors on GPU for fast value iteration.
        
        Returns:
            actions_per_state: List of lists of actions for each state
            rewards: Dict mapping (state_idx, action_idx) -> reward tensor
            transitions: Dict mapping (state_idx, action_idx) -> (next_state_indices, probabilities)
        """
        print("Building transition matrices...")
        
        actions_per_state = []
        rewards = {}
        transitions = {}
        
        state_iter = enumerate(self.states)
        if show_progress and tqdm:
            state_iter = tqdm(state_iter, total=self.num_states, desc="Building transitions")
        
        for state_idx, state in state_iter:
            if self.is_terminal(state):
                actions_per_state.append([])
                continue
            
            actions = self.get_actions(state)
            actions_per_state.append(actions)
            
            for action_idx, action in enumerate(actions):
                reward, next_dist = self.simulate_shot(state, action, num_samples)
                
                next_indices = []
                probs = []
                
                for next_state, prob in next_dist.items():
                    if next_state in self.state_to_idx:
                        next_indices.append(self.state_to_idx[next_state])
                        probs.append(prob)
                
                rewards[(state_idx, action_idx)] = reward
                transitions[(state_idx, action_idx)] = (
                    torch.tensor(next_indices, dtype=torch.long, device=self.device),
                    torch.tensor(probs, dtype=torch.float32, device=self.device)
                )
        
        print(f"Built transitions for {self.num_states} states")
        return actions_per_state, rewards, transitions
    
    def value_iteration_gpu(
        self, 
        actions_per_state, 
        rewards, 
        transitions,
        max_iterations=100,
        gamma=0.99,
        epsilon=1e-6,
        show_progress=True
    ):
        """
        GPU-accelerated value iteration.
        
        Args:
            actions_per_state: Output from build_transition_matrices
            rewards: Reward dict from build_transition_matrices
            transitions: Transition dict from build_transition_matrices
            max_iterations: Max iterations
            gamma: Discount factor
            epsilon: Convergence threshold
            show_progress: Show progress bar
        
        Returns:
            value_function: Dict mapping states to values
            policy: Dict mapping states to best actions
        """
        V = torch.zeros(self.num_states, dtype=torch.float32, device=self.device)
        
        iter_range = range(max_iterations)
        if show_progress and tqdm:
            iter_range = tqdm(iter_range, desc="Value iteration")
        
        for iteration in iter_range:
            V_old = V.clone()
            max_delta = 0.0
            
            for state_idx in range(self.num_states):
                if not actions_per_state[state_idx]:
                    continue
                
                action_values = []
                
                for action_idx in range(len(actions_per_state[state_idx])):
                    r = rewards[(state_idx, action_idx)]
                    next_indices, probs = transitions[(state_idx, action_idx)]
                    
                    next_values = V_old[next_indices]
                    expected_next_value = torch.sum(probs * next_values).item()
                    
                    q_value = r + gamma * expected_next_value
                    action_values.append(q_value)
                
                if action_values:
                    V[state_idx] = max(action_values)
            
            delta = torch.max(torch.abs(V - V_old)).item()
            max_delta = delta
            
            if show_progress and tqdm and hasattr(iter_range, 'set_postfix'):
                iter_range.set_postfix({'delta': f'{delta:.6f}'})
            
            if delta < epsilon:
                print(f"\nConverged after {iteration + 1} iterations")
                break
        
        value_function = {self.states[i]: V[i].item() for i in range(self.num_states)}
        
        policy = {}
        for state_idx in range(self.num_states):
            state = self.states[state_idx]
            
            if not actions_per_state[state_idx]:
                policy[state] = None
                continue
            
            best_action = None
            best_value = float('-inf')  # ← Start at negative infinity

            for action_idx, action in enumerate(actions_per_state[state_idx]):
                r = rewards[(state_idx, action_idx)]
                next_indices, probs = transitions[(state_idx, action_idx)]
                next_values = V[next_indices]
                expected_next_value = torch.sum(probs * next_values).item()
                q_value = r + gamma * expected_next_value
                
                if q_value > best_value:
                    best_value = q_value
                    best_action = action

            policy[state] = best_action
        
        return value_function, policy
    
    def solve(self, num_samples=100, max_iterations=100, gamma=0.99, epsilon=1e-6):
        """
        Complete solve: build transitions and run value iteration.
        
        Returns:
            (value_function, policy)
        """
        actions, rewards, transitions = self.build_transition_matrices(num_samples)
        value_function, policy = self.value_iteration_gpu(
            actions, rewards, transitions, max_iterations, gamma, epsilon
        )
        self.value_function = value_function
        self.policy = policy
        return value_function, policy
    
    def save(self, id, overwrite=True):
        if self.value_function is None or self.policy is None:
            raise ValueError("MDP must be solved before saving. value_function and policy cannot be None.")

        file_path = MDP_DIR / f"{id}.json"
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"MDP file already exists: {file_path}")

        value_function_rows = [
            {
                "state": [float(state[0]), float(state[1])],
                "value": float(value),
            }
            for state, value in self.value_function.items()
        ]

        policy_rows = []
        for state, action in self.policy.items():
            entry = {"state": [float(state[0]), float(state[1])], "action": None}
            if action is not None:
                entry["action"] = {
                    "club_idx": int(action[0]),
                    "target_x": float(action[1]),
                    "target_y": float(action[2]),
                }
            policy_rows.append(entry)

        payload = {
            "id": id,
            "grid_step": float(self.grid_step),
            "club_ids": list(self.club_ids),
            "value_function": value_function_rows,
            "policy": policy_rows,
        }

        MDP_DIR.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)

        return self

    def load(self, id):
        file_path = MDP_DIR / f"{id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"MDP file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as json_file:
            payload = json.load(json_file)

        if payload.get("id") != id:
            raise ValueError(f"MDP id mismatch: expected '{id}', found '{payload.get('id')}'.")

        self.grid_step = float(payload["grid_step"])
        self.club_ids = list(payload["club_ids"])
        self.num_clubs = len(self.club_ids)

        loaded_value_function = {}
        for row in payload["value_function"]:
            state = row["state"]
            loaded_value_function[(float(state[0]), float(state[1]))] = float(row["value"])

        loaded_policy = {}
        for row in payload["policy"]:
            state = row["state"]
            state_key = (float(state[0]), float(state[1]))
            action = row["action"]
            if action is None:
                loaded_policy[state_key] = None
            else:
                loaded_policy[state_key] = (
                    int(action["club_idx"]),
                    float(action["target_x"]),
                    float(action["target_y"]),
                )

        self.value_function = loaded_value_function
        self.policy = loaded_policy

        return self
    
    def get_policy_for_state(self, state):
        x, y = state
        if x % self.grid_step != 0 or y % self.grid_step != 0:
            raise ValueError(f"State ({x}, {y}) is not on the grid. Must be multiples of grid_step {self.grid_step}.")
        
        if self.policy is None:
            raise ValueError("Policy not available. Solve the MDP first.")
        return self.policy.get(state, None)

    def get_expected_value_for_state(self, state):
        x, y = state
        if x % self.grid_step != 0 or y % self.grid_step != 0:
            raise ValueError(f"State ({x}, {y}) is not on the grid. Must be multiples of grid_step {self.grid_step}.")
        
        if self.value_function is None:
            raise ValueError("Value function not available. Solve the MDP first.")
        return self.value_function.get(state, None)