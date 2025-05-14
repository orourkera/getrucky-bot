# tests/test_all.py

import unittest
from unittest.mock import Mock, patch
import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api_client
import content_generator
import interaction_handler
import scheduler
import cross_post
import health
from config import get_config

class TestAPIClient(unittest.TestCase):
    def setUp(self):
        self.mock_x_client = Mock()
        self.mock_xai_headers = {'Authorization': 'Bearer test_key'}
    
    @patch('api_client.tweepy.Client')
    def test_initialize_x_client(self, mock_tweepy):
        """Test X client initialization."""
        mock_tweepy.return_value = self.mock_x_client
        client = api_client.initialize_x_client()
        self.assertIsNotNone(client)
        mock_tweepy.assert_called_once()
    
    @patch('api_client.requests.post')
    def test_generate_text(self, mock_post):
        """Test xAI text generation."""
        mock_response = Mock()
        mock_response.json.return_value = {'text': 'Test response'}
        mock_post.return_value = mock_response
        
        response = api_client.generate_text(self.mock_xai_headers, 'Test prompt')
        self.assertEqual(response, 'Test response')
        mock_post.assert_called_once()

class TestContentGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_xai_headers = {'Authorization': 'Bearer test_key'}
        self.mock_session_data = {
            'user': 'test_user',
            'distance': 10.5,
            'duration': 120,
            'location': 'Test Location',
            'achievements': ['double_digit', 'streak_7']
        }
    
    @patch('content_generator.api_client.generate_text')
    def test_generate_session_post(self, mock_generate):
        """Test session post generation."""
        mock_generate.return_value = 'Test session post'
        post = content_generator.generate_session_post(self.mock_xai_headers, self.mock_session_data)
        self.assertIsNotNone(post)
        self.assertIn('test_user', post.lower())
        self.assertIn('10.5', post)
    
    def test_select_content_type(self):
        """Test content type selection."""
        content_type = content_generator.select_content_type()
        self.assertIn(content_type, ['pun', 'challenge', 'theme', 'poll', 'meme', 'shoutout', 'ugc'])

class TestInteractionHandler(unittest.TestCase):
    def setUp(self):
        self.mock_x_client = Mock()
        self.mock_xai_headers = {'Authorization': 'Bearer test_key'}
        self.test_tweet = "Just finished a great ruck! @getrucky"
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis."""
        sentiment, context = interaction_handler.analyze_sentiment(self.test_tweet)
        self.assertIn(sentiment, ['very_positive', 'positive', 'neutral', 'negative', 'very_negative'])
        self.assertIsInstance(context, dict)
        self.assertIn('is_question', context)
        self.assertIn('has_rucking_mention', context)
    
    @patch('interaction_handler.api_client.generate_text')
    def test_generate_reply(self, mock_generate):
        """Test reply generation."""
        mock_generate.return_value = 'Test reply'
        reply = interaction_handler.generate_reply(
            self.mock_xai_headers,
            self.test_tweet,
            'positive',
            'challenge',
            {'is_question': False, 'has_rucking_mention': True}
        )
        self.assertIsNotNone(reply)
        self.assertIn('@getrucky', reply.lower())

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.mock_scheduler = Mock()
        self.mock_x_client = Mock()
        self.mock_app_client = Mock()
        self.mock_xai_client = Mock()
    
    def test_schedule_posts(self):
        """Test post scheduling."""
        scheduler.schedule_posts(
            self.mock_scheduler,
            self.mock_x_client,
            self.mock_app_client,
            self.mock_xai_client
        )
        self.assertTrue(self.mock_scheduler.add_job.called)
    
    def test_schedule_engagement(self):
        """Test engagement scheduling."""
        scheduler.schedule_engagement(
            self.mock_scheduler,
            self.mock_x_client,
            self.mock_xai_client
        )
        self.assertTrue(self.mock_scheduler.add_job.called)

class TestCrossPost(unittest.TestCase):
    def setUp(self):
        self.mock_x_client = Mock()
        self.mock_xai_headers = {'Authorization': 'Bearer test_key'}
    
    @patch('cross_post.api_client.search_tweets')
    def test_engage_with_posts(self, mock_search):
        """Test post engagement."""
        mock_search.return_value = [
            {'id': '123', 'text': 'Test ruck post', 'user': {'followers_count': 2000}}
        ]
        cross_post.engage_with_posts()
        self.assertTrue(mock_search.called)

class TestHealth(unittest.TestCase):
    def setUp(self):
        self.mock_x_client = Mock()
        self.mock_x_client.get_me.return_value = Mock(screen_name='test_user', followers_count=1000)
    
    @patch('health.api_client.generate_text')
    def test_get_health_status(self, mock_generate):
        """Test health status check."""
        mock_generate.return_value = 'Test response'
        status = health.get_health_status(self.mock_x_client)
        self.assertIsNotNone(status)
        self.assertIn('timestamp', status)
        self.assertIn('databases', status)
        self.assertIn('apis', status)
        self.assertIn('system', status)
        self.assertIn('overall_status', status)

if __name__ == '__main__':
    unittest.main() 