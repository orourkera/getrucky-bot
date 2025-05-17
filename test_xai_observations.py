#!/usr/bin/env python
# test_xai_observations.py - Script to test XAI observations with mock data

import logging
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock
import content_generator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample XAI observation responses for different session types
SAMPLE_OBSERVATIONS = {
    'short_distance': [
        "Impressive pace for a short distance, showing great intensity!",
        "Great effort on a quick ruck - maintaining that pace is challenging!",
        "Short but effective session with consistent pacing throughout."
    ],
    'long_distance': [
        "Marathon-level endurance demonstrated in this epic ruck!",
        "Incredible distance covered with remarkable consistency.",
        "Outstanding long-haul performance showing true rucking dedication!"
    ],
    'heavy_weight': [
        "Carrying that weight for this distance is truly impressive!",
        "Heavy load successfully managed - great strength training!",
        "Exceptional strength demonstrated with that heavy pack!"
    ],
    'high_elevation': [
        "Conquered some serious elevation - your legs must be feeling it!",
        "Those hills were no match for your determination today.",
        "Impressive vertical gain on this challenging route!"
    ],
    'slow_pace': [
        "Steady, consistent pace - perfect for building endurance.",
        "Great example of the 'slow and steady' approach to rucking.",
        "Maintaining that consistent pace shows excellent discipline."
    ],
    'fast_pace': [
        "Blazing fast pace - almost at running speed with that pack!",
        "Speed demon alert! Outstanding pace for a weighted ruck.",
        "That's a tempo ruck if I've ever seen one - fantastic pace!"
    ],
    'default': [
        "Solid effort demonstrating great rucking form!",
        "Well-executed ruck with good overall metrics.",
        "A balanced session hitting all the key components of a good ruck."
    ]
}

def get_mock_observation(session_data):
    """Get a mock observation based on session characteristics."""
    # Extract data
    distance = float(session_data.get('distance', 0))
    weight = float(session_data.get('ruck_weight', 0))
    elevation = float(session_data.get('elevation_gain', 0))
    pace_str = session_data.get('pace', 'N/A')
    
    # Parse pace if available
    if pace_str and pace_str != 'N/A':
        try:
            pace_parts = pace_str.split(':')
            pace_minutes = int(pace_parts[0])
        except:
            pace_minutes = 15  # Default moderate pace
    else:
        pace_minutes = 15
    
    # Determine session type
    if distance >= 10:
        session_type = 'long_distance'
    elif distance < 3:
        session_type = 'short_distance'
    elif weight >= 20:
        session_type = 'heavy_weight'
    elif elevation >= 200:
        session_type = 'high_elevation'
    elif pace_minutes < 12:
        session_type = 'fast_pace'
    elif pace_minutes > 18:
        session_type = 'slow_pace'
    else:
        session_type = 'default'
    
    # Select a random observation from the appropriate category
    import random
    observations = SAMPLE_OBSERVATIONS.get(session_type, SAMPLE_OBSERVATIONS['default'])
    return random.choice(observations)

def test_with_mocked_session(session_type='default'):
    """Test XAI observations with a mocked session."""
    try:
        # Create mock session data based on session type
        if session_type == 'long_distance':
            session_data = {
                'distance': '12.5',
                'duration': '3h 15m',
                'ruck_weight': '15',
                'elevation_gain': '120',
                'pace': '15:30'
            }
            title = "LONG DISTANCE SESSION"
        elif session_type == 'heavy_weight':
            session_data = {
                'distance': '5.2',
                'duration': '1h 45m',
                'ruck_weight': '30',
                'elevation_gain': '85',
                'pace': '20:10'
            }
            title = "HEAVY WEIGHT SESSION"
        elif session_type == 'high_elevation':
            session_data = {
                'distance': '6.8',
                'duration': '2h 30m',
                'ruck_weight': '10',
                'elevation_gain': '350',
                'pace': '22:05'
            }
            title = "HIGH ELEVATION SESSION"
        elif session_type == 'fast_pace':
            session_data = {
                'distance': '4.5',
                'duration': '0h 45m',
                'ruck_weight': '5',
                'elevation_gain': '30',
                'pace': '10:00'
            }
            title = "FAST PACE SESSION"
        else:  # default/balanced session
            session_data = {
                'distance': '5.0',
                'duration': '1h 20m',
                'ruck_weight': '10',
                'elevation_gain': '75',
                'pace': '16:00'
            }
            title = "TYPICAL BALANCED SESSION"
        
        # Add default fields
        session_data.update({
            'user': 'test-user',
            'city': 'Austin',
            'state': 'TX',
            'country': 'USA',
            'session_id': '999',
            'date': datetime.now().isoformat()
        })
        
        # Mock the XAI client and response
        mock_observation = get_mock_observation(session_data)
        
        # Patch the XAI API call in content_generator
        with patch('api_client.initialize_xai_client') as mock_init_xai:
            with patch('api_client.generate_text') as mock_generate_text:
                # Configure mocks
                mock_init_xai.return_value = {'mocked': 'headers'}
                mock_generate_text.return_value = mock_observation
                
                # Set XAI_API_KEY in environment
                import os
                os.environ['XAI_API_KEY'] = 'mock_key'
                
                # Generate post text
                post_text = content_generator.generate_map_post_text(session_data)
                
                # Add timestamp
                current_time = datetime.now().strftime('%H:%M')
                post_text = f"{post_text} [{current_time}]"
                
                # Print the result
                print("\n" + "="*80)
                print(f"{title}:")
                print("="*80)
                for key, value in session_data.items():
                    if key in ['distance', 'duration', 'ruck_weight', 'elevation_gain', 'pace']:
                        print(f"{key}: {value}")
                
                print("\n" + "="*80)
                print("GENERATED OBSERVATION:")
                print("="*80)
                print(mock_observation)
                
                print("\n" + "="*80)
                print("TWEET PREVIEW:")
                print("="*80)
                print(post_text)
                print("="*80 + "\n")
                
                logger.info(f"Tweet content: {post_text}")
                logger.info(f"Tweet length: {len(post_text)} characters")
                
                return True
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to run XAI observation tests."""
    # Get session type from command line if provided
    session_type = 'default'
    if len(sys.argv) > 1:
        session_type = sys.argv[1]
        
    if session_type == 'all':
        # Test all session types
        session_types = ['default', 'long_distance', 'heavy_weight', 'high_elevation', 'fast_pace']
        for session_type in session_types:
            print(f"\n\n{'#'*40} TESTING {session_type.upper()} {'#'*40}\n")
            test_with_mocked_session(session_type)
    else:
        # Test specific session type
        test_with_mocked_session(session_type)
    
    return True

if __name__ == "__main__":
    success = main()
    print(f"XAI observation test {'succeeded' if success else 'failed'}") 