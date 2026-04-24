"""
Optimized Markov Decision Process for golf hole simulation.

Key optimizations:
- Precompute and cache shot samples for all (state, action) pairs
- Vectorize collision/hazard detection
- Cache terminal states and action spaces
- Use numpy operations instead of loops where possible
"""

import numpy as np
from pathlib import Path
import sys
import time
from functools import lru_cache
from collections import defaultdict

try:
    from tqdm.auto import tqdm
except ImportError:
    tqdm = None

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Simulation.holecomponent import HoleComponent
from Simulation.golfhole import Hole
from Models.GaussianMixture import gaussian_mixture_model


class GolfHoleMDP:
    """Optimized MDP for golf hole play."""
    
    def __init__(self, hole, gmm_list):
        self.hole = hole
        self.gmm_list = gmm_list
        self.num_clubs = len(gmm_list)
        self.pin_location = np.array(hole.pin_location)
        self.tee_location = np.array(hole.tee_location)
        
        self.hole_width = hole.x
        self.hole_depth = hole.y
        self.x_min = -self.hole_width / 2
        self.x_max = self.hole_width / 2
        self.y_min = 0
        self.y_max = self.hole_depth
        self.grid_step = 10
        
        # Precompute components by type for faster lookup
        self._component_cache = {}
        for comp_type in ['tree', 'water', 'bunker', 'green', 'pin']:
            self._component_cache[comp_type] = self._find_component_by_type(comp_type)
        
        # Cache for precomputed samples
        self._sample_cache = {}
        
        # Cache for terminal states
        self._terminal_state_cache = {}
        
        # Precompute all discrete states
        state_grid_x = np.arange(self.x_min, self.x_max + 1e-9, self.grid_step)
        state_grid_y = np.arange(self.y_min, self.y_max + 1e-9, self.grid_step)
        self.all_states = [(float(x), float(y)) for x in state_grid_x for y in state_grid_y]
        
        print(f"Initialized MDP with {len(self.all_states)} discrete states")

    def _snap_to_grid(self, x, y):
        gx = round((x - self.x_min) / self.grid_step) * self.grid_step + self.x_min
        gy = round((y - self.y_min) / self.grid_step) * self.grid_step + self.y_min
        return (float(gx), float(gy))
    
    def _find_component_by_type(self, comp_type):
        return [comp for comp in self.hole.components if comp.type == comp_type]
    
    def _is_out_of_bounds(self, x, y):
        return x < self.x_min or x > self.x_max or y < self.y_min or y > self.y_max
    
    def _ball_hits_component(self, x_start, y_start, x_end, y_end, comp_type):
        components = self._component_cache.get(comp_type, [])
        hit_components = []
        for comp in components:
            if comp.intersects_segment(x_start, y_start, x_end, y_end):
                hit_components.append(comp)
        return hit_components

    def _ball_lands_on_component(self, x_end, y_end, comp_type):
        components = self._component_cache.get(comp_type, [])
        landed_components = []
        for comp in components:
            if comp.contains(x_end, y_end):
                landed_components.append(comp)
        return landed_components
    
    def _get_sample_cache_key(self, x_start, y_start, club_index, target_x, target_y, num_samples):
        """Create hashable cache key for shot samples."""
        return (
            round(x_start, 2), round(y_start, 2),
            club_index,
            round(target_x, 2), round(target_y, 2),
            num_samples
        )
    
    def _sample_shot(self, x_start, y_start, club_index, target_x, target_y, num_samples=100):
        """
        Sample shot trajectories with caching.
        OPTIMIZATION: Cache results to avoid re-sampling identical shots.
        """
        cache_key = self._get_sample_cache_key(x_start, y_start, club_index, target_x, target_y, num_samples)
        
        if cache_key in self._sample_cache:
            return self._sample_cache[cache_key]
        
        gmm = self.gmm_list[club_index]
        samples = gmm.sample(num_samples)[0]
        
        target_dir = np.array([target_x - x_start, target_y - y_start])
        target_dist = np.linalg.norm(target_dir)
        
        if target_dist < 1e-6:
            target_dir = np.array([0, 1])
        else:
            target_dir = target_dir / target_dist
        
        # Vectorized computation of all landings
        perp_dir = np.array([-target_dir[1], target_dir[0]])
        start_pos = np.array([x_start, y_start])
        
        # Compute all landings at once using broadcasting
        distances = samples[:, 1][:, np.newaxis]  # Shape (num_samples, 1)
        laterals = samples[:, 0][:, np.newaxis]   # Shape (num_samples, 1)
        
        landings = (start_pos + 
                   distances * target_dir + 
                   laterals * perp_dir)
        
        result = [(float(x), float(y)) for x, y in landings]
        self._sample_cache[cache_key] = result
        return result
    
    def _process_landing_vectorized(self, x_start, y_start, landings):
        """
        Process multiple landings with consistent terminal state handling.
        """
        stroke_penalty = -1
        results = []
        
        # Convert to numpy arrays for vectorized operations
        landings_array = np.array(landings)
        x_ends = landings_array[:, 0]
        y_ends = landings_array[:, 1]
        
        # Vectorized out-of-bounds check
        oob_mask = ((x_ends < self.x_min) | (x_ends > self.x_max) | 
                    (y_ends < self.y_min) | (y_ends > self.y_max))
        
        for i, (x_end, y_end) in enumerate(landings):
            reward = stroke_penalty
            
            if oob_mask[i]:
                reward -= 2
                next_state = (x_start, y_start) 
            elif (self._ball_hits_component(x_start, y_start, x_end, y_end, 'tree') or 
                self._ball_lands_on_component(x_end, y_end, 'tree')):
                reward -= 2
                next_state = (x_start, y_start)
            elif self._ball_lands_on_component(x_end, y_end, 'bunker'):
                reward -= 2
                next_state = self._snap_to_grid(x_end, y_end)
            elif self._ball_lands_on_component(x_end, y_end, 'water'):
                reward -= 1
                next_state = self._snap_to_grid(x_start, y_start)
            else:
                # Calculate distance to pin
                pin_distance = np.linalg.norm(np.array([x_end, y_end]) - self.pin_location)
                
                # Terminal state: ball is close enough to hole
                if pin_distance < 7.0:
                    # No additional penalty - they holed it
                    next_state = self._get_terminal_state()  # Use canonical terminal state
                # On green but not in hole (within 30 yards): assume 2-putt
                elif self._ball_lands_on_component(x_end, y_end, 'green') or pin_distance < 30:
                    reward -= 2  # This shot + 2 more putts = -3 total
                    next_state = self._get_terminal_state()
                # Close but not on green (30-50 yards): assume chip + 2-putt  
                elif pin_distance < 50:
                    reward -= 3  # This shot + chip + 2 putts = -4 total
                    next_state = self._get_terminal_state()
                # Normal landing on fairway
                else:
                    next_state = self._snap_to_grid(x_end, y_end)
            
            results.append((reward, next_state))
        
        return results

    def _get_terminal_state(self):
        """
        Return the canonical terminal state.
        This ensures all paths to completion go to the SAME state.
        """
        # Use a state that will definitely pass is_terminal_state() check
        return tuple(self.pin_location)

    def is_terminal_state(self, state):
        """
        Check if state is terminal (ball is holed).
        A state is terminal if it's at the pin location.
        """
        if state not in self._terminal_state_cache:
            # Terminal = exactly at pin location (where we teleport completed balls)
            self._terminal_state_cache[state] = (
                state[0] == self.pin_location[0] and 
                state[1] == self.pin_location[1]
            )
        return self._terminal_state_cache[state]

    def _is_at_hole(self, x, y):
        """Check if position is at the hole (used during landing processing)."""
        return np.linalg.norm(np.array([x, y]) - self.pin_location) < 30
        
    def step(self, state, action, num_samples=100):
        """
        Execute one step with optimized processing.
        OPTIMIZATION: Vectorize landing processing and cache samples.
        """
        x_start, y_start = state
        club_index, target_x, target_y = action
        
        # Get samples (cached if previously computed)
        landings = self._sample_shot(x_start, y_start, club_index, target_x, target_y, num_samples)
        
        # Process landings in vectorized manner
        landing_results = self._process_landing_vectorized(x_start, y_start, landings)
        
        # Accumulate results
        next_state_dist = defaultdict(int)
        total_reward = 0
        
        for reward, next_state in landing_results:
            total_reward += reward
            next_state_dist[next_state] += 1
        
        # Normalize to probabilities
        next_state_dist = {k: v / num_samples for k, v in next_state_dist.items()}
        expected_reward = total_reward / num_samples
        
        return expected_reward, next_state_dist
        

    
    
    def get_possible_actions(self, state, num_angle_samples=5):
        """
        Generate sensible actions aimed toward the hole.
        """
        actions = []
        x, y = state
        
        # Vector to pin
        to_pin = self.pin_location - np.array([x, y])
        dist_to_pin = np.linalg.norm(to_pin)
        
        # Don't generate actions if already at pin
        if dist_to_pin < 1e-6:
            return actions
        
        # Base direction toward pin
        pin_direction = to_pin / dist_to_pin
        pin_angle = np.arctan2(pin_direction[1], pin_direction[0])
        
        for club_idx in range(self.num_clubs):
            # Action 1: Aim directly at pin
            actions.append((
                club_idx, 
                float(self.pin_location[0]), 
                float(self.pin_location[1])
            ))
            
            # Actions 2-N: Aim at angles around the pin direction
            # Use smaller spread for accuracy
            angle_spread = np.pi / 8  # ±22.5 degrees
            angle_offsets = np.linspace(-angle_spread, angle_spread, num_angle_samples)
            
            for offset in angle_offsets:
                angle = pin_angle + offset
                
                # Aim point at some distance in this direction
                # Use distance to pin as aim distance (or cap it)
                aim_dist = min(dist_to_pin * 1.2, 150)  # Don't aim too far past
                
                target_x = x + aim_dist * np.cos(angle)
                target_y = y + aim_dist * np.sin(angle)
                
                # Only add if target is reasonable (forward progress toward pin)
                target_to_pin = np.linalg.norm(self.pin_location - np.array([target_x, target_y]))
                if target_to_pin < dist_to_pin * 1.5:  # Don't aim way past the pin
                    actions.append((club_idx, float(target_x), float(target_y)))
        
        return actions
    
    def precompute_transitions(self, num_samples=100, show_progress=True):
        """
        MAJOR OPTIMIZATION: Precompute all state-action transitions before value iteration.
        This eliminates redundant sampling during VI.
        """
        print(f"Precomputing transitions for {len(self.all_states)} states...")
        self._transition_cache = {}
        
        state_iter = self.all_states
        if show_progress and tqdm is not None:
            state_iter = tqdm(state_iter, desc="Precomputing transitions", unit="state")
        
        for state in state_iter:
            if self.is_terminal_state(state):
                continue
            
            actions = self.get_possible_actions(state, num_angle_samples=5)
            
            for action in actions:
                cache_key = (state, action)
                expected_reward, next_state_dist = self.step(state, action, num_samples=num_samples)
                self._transition_cache[cache_key] = (expected_reward, next_state_dist)
        
        print(f"Cached {len(self._transition_cache)} state-action transitions")
    
    def value_iteration(
        self,
        max_iterations=100,
        discount_factor=0.99,
        epsilon=1e-6,
        show_progress=True,
        show_state_progress=False,  # Disabled by default since it's slow
        num_angle_samples=5,
        num_samples=5,
    ):
        """
        Optimized value iteration using precomputed transitions.
        """
        # Precompute transitions if not already done
        if not hasattr(self, '_transition_cache'):
            self.precompute_transitions(num_samples=num_samples, show_progress=show_progress)
        
        value_function = {state: 0.0 for state in self.all_states}
        
        iteration_iterable = range(max_iterations)
        if show_progress and tqdm is not None:
            iteration_iterable = tqdm(iteration_iterable, desc="Value iteration", unit="iter")
        
        for iteration in iteration_iterable:
            max_diff = 0.0
            
            for state in self.all_states:
                if self.is_terminal_state(state):
                    continue
                
                old_value = value_function[state]
                best_value = float('inf')
                
                actions = self.get_possible_actions(state, num_angle_samples=num_angle_samples)
                
                for action in actions:
                    cache_key = (state, action)
                    
                    if cache_key in self._transition_cache:
                        expected_reward, next_state_dist = self._transition_cache[cache_key]
                    else:
                        # Fallback if not cached (shouldn't happen after precompute)
                        expected_reward, next_state_dist = self.step(state, action, num_samples=num_samples)
                    
                    # Expected value of next states
                    next_value = sum(prob * value_function.get(next_state, 0.0) 
                                    for next_state, prob in next_state_dist.items())
                    
                    action_value = expected_reward + discount_factor * next_value
                    best_value = min(best_value, action_value)
                
                value_function[state] = best_value
                max_diff = max(max_diff, abs(value_function[state] - old_value))
            
            if show_progress and tqdm is not None and hasattr(iteration_iterable, "set_postfix"):
                iteration_iterable.set_postfix({"max_diff": f"{max_diff:.3g}"})
            
            if max_diff < epsilon:
                if show_progress:
                    print(f"\nValue iteration converged after {iteration + 1} iterations")
                break
        
        return value_function
    
    def _find_nearest_state(self, position, state_list):
        if not state_list:
            return position
        
        position = np.array(position)
        distances = [np.linalg.norm(np.array(s) - position) for s in state_list]
        nearest_idx = np.argmin(distances)
        return state_list[nearest_idx]