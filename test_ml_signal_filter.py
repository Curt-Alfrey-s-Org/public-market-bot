#!/usr/bin/env python3
"""
Test suite for ML Signal Filter module
Tests machine learning signal filtering and risk assessment functionality
"""

import unittest
import os
import numpy as np
import tempfile
from ml_signal_filter import MLSignalFilter, MLRiskAssessor, SKLEARN_AVAILABLE


class TestMLSignalFilter(unittest.TestCase):
    """Test cases for MLSignalFilter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not SKLEARN_AVAILABLE:
            self.skipTest("scikit-learn not available")
        
        # Create sample training data
        np.random.seed(42)
        self.training_data = []
        self.labels = []
        
        for i in range(100):
            signal_data = {
                'signal': 'BUY' if i % 2 == 0 else 'SELL',
                'price': 100 + np.random.randn() * 10,
                'indicators': {
                    'rsi': 30 + np.random.randn() * 20,
                    'macd': np.random.randn(),
                    'macd_signal': np.random.randn(),
                    'macd_histogram': np.random.randn() * 0.5,
                    'bb_upper': 105,
                    'bb_middle': 100,
                    'bb_lower': 95,
                    'sma_fast': 100 + np.random.randn() * 5,
                    'sma_slow': 100 + np.random.randn() * 3,
                    'momentum': np.random.randn() * 0.05,
                    'atr': 2 + np.random.randn(),
                    'adx': 25 + np.random.randn() * 10,
                    'stoch_k': 50 + np.random.randn() * 20
                }
            }
            
            # Generate label with some correlation to RSI
            rsi = signal_data['indicators']['rsi']
            win_prob = 0.7 if (rsi < 35 or rsi > 65) else 0.4
            label = 1 if np.random.rand() < win_prob else 0
            
            self.training_data.append(signal_data)
            self.labels.append(label)
    
    def test_initialization_random_forest(self):
        """Test MLSignalFilter initialization with Random Forest"""
        filter_model = MLSignalFilter(model_type='random_forest')
        
        self.assertTrue(filter_model.enabled)
        self.assertEqual(filter_model.model_type, 'random_forest')
        self.assertFalse(filter_model.is_trained)
        self.assertIsNotNone(filter_model.model)
    
    def test_initialization_gradient_boosting(self):
        """Test MLSignalFilter initialization with Gradient Boosting"""
        filter_model = MLSignalFilter(model_type='gradient_boosting')
        
        self.assertTrue(filter_model.enabled)
        self.assertEqual(filter_model.model_type, 'gradient_boosting')
        self.assertFalse(filter_model.is_trained)
        self.assertIsNotNone(filter_model.model)
    
    def test_feature_extraction(self):
        """Test feature extraction from signal data"""
        filter_model = MLSignalFilter(model_type='random_forest')
        
        signal_data = self.training_data[0]
        features = filter_model.extract_features(signal_data)
        
        self.assertIsNotNone(features)
        self.assertGreater(len(features.columns), 0)
        self.assertEqual(len(features), 1)  # One row
    
    def test_feature_extraction_missing_data(self):
        """Test feature extraction with missing indicator data"""
        filter_model = MLSignalFilter(model_type='random_forest')
        
        # Minimal signal data
        signal_data = {
            'signal': 'BUY',
            'price': 100,
            'indicators': {}
        }
        
        features = filter_model.extract_features(signal_data)
        
        self.assertIsNotNone(features)
        self.assertGreater(len(features.columns), 0)
    
    def test_model_training(self):
        """Test model training with valid data"""
        filter_model = MLSignalFilter(model_type='random_forest')
        
        metrics = filter_model.train(self.training_data, self.labels)
        
        self.assertTrue(filter_model.is_trained)
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1', metrics)
        self.assertIn('auc', metrics)
        
        # Check that metrics are reasonable
        self.assertGreaterEqual(metrics['accuracy'], 0.0)
        self.assertLessEqual(metrics['accuracy'], 1.0)
    
    def test_predict_before_training(self):
        """Test prediction before model is trained"""
        filter_model = MLSignalFilter(model_type='random_forest')
        
        test_signal = self.training_data[0]
        confidence, win_prob = filter_model.predict_signal_quality(test_signal)
        
        # Should return default values
        self.assertEqual(confidence, 0.5)
        self.assertEqual(win_prob, 0.5)
    
    def test_predict_after_training(self):
        """Test prediction after model is trained"""
        filter_model = MLSignalFilter(model_type='random_forest')
        filter_model.train(self.training_data, self.labels)
        
        test_signal = self.training_data[0]
        confidence, win_prob = filter_model.predict_signal_quality(test_signal)
        
        # Should return valid probabilities
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertGreaterEqual(win_prob, 0.0)
        self.assertLessEqual(win_prob, 1.0)
    
    def test_signal_filtering(self):
        """Test signal filtering logic"""
        filter_model = MLSignalFilter(model_type='random_forest')
        filter_model.train(self.training_data, self.labels)
        
        test_signal = self.training_data[0]
        
        # Test with high thresholds (should filter)
        should_filter, scores = filter_model.should_filter_signal(
            test_signal, min_confidence=0.9, min_win_prob=0.9
        )
        
        self.assertIsInstance(should_filter, bool)
        self.assertIn('confidence', scores)
        self.assertIn('win_probability', scores)
    
    def test_feature_importance(self):
        """Test feature importance tracking"""
        filter_model = MLSignalFilter(model_type='random_forest')
        filter_model.train(self.training_data, self.labels)
        
        self.assertIsNotNone(filter_model.feature_importance)
        self.assertGreater(len(filter_model.feature_importance), 0)
        
        # Check that importances sum to approximately 1
        total_importance = sum(filter_model.feature_importance.values())
        self.assertAlmostEqual(total_importance, 1.0, places=2)
    
    def test_model_save_and_load(self):
        """Test saving and loading trained model"""
        filter_model = MLSignalFilter(model_type='random_forest')
        filter_model.train(self.training_data, self.labels)
        
        # Save model
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
            model_path = tmp.name
        
        try:
            filter_model.save_model(model_path)
            self.assertTrue(os.path.exists(model_path))
            
            # Load model
            loaded_model = MLSignalFilter(model_type='random_forest', model_path=model_path)
            
            self.assertTrue(loaded_model.is_trained)
            self.assertEqual(loaded_model.model_type, 'random_forest')
            
            # Test that predictions match
            test_signal = self.training_data[0]
            conf1, prob1 = filter_model.predict_signal_quality(test_signal)
            conf2, prob2 = loaded_model.predict_signal_quality(test_signal)
            
            self.assertAlmostEqual(conf1, conf2, places=5)
            self.assertAlmostEqual(prob1, prob2, places=5)
            
        finally:
            if os.path.exists(model_path):
                os.remove(model_path)
    
    def test_different_model_types(self):
        """Test that both Random Forest and Gradient Boosting work"""
        for model_type in ['random_forest', 'gradient_boosting']:
            filter_model = MLSignalFilter(model_type=model_type)
            metrics = filter_model.train(self.training_data, self.labels)
            
            self.assertTrue(filter_model.is_trained)
            self.assertGreater(metrics['accuracy'], 0.0)


class TestMLRiskAssessor(unittest.TestCase):
    """Test cases for MLRiskAssessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not SKLEARN_AVAILABLE:
            self.skipTest("scikit-learn not available")
        
        self.risk_assessor = MLRiskAssessor()
    
    def test_initialization(self):
        """Test MLRiskAssessor initialization"""
        self.assertTrue(self.risk_assessor.enabled)
    
    def test_risk_assessment_basic(self):
        """Test basic risk assessment"""
        signal_data = {
            'signal': 'BUY',
            'price': 100,
            'indicators': {
                'rsi': 50,
                'atr': 2.0,
                'adx': 25,
                'momentum': 0.02
            }
        }
        
        risk_metrics = self.risk_assessor.assess_trade_risk(signal_data)
        
        self.assertIn('risk_score', risk_metrics)
        self.assertIn('volatility_risk', risk_metrics)
        self.assertIn('momentum_risk', risk_metrics)
        self.assertIn('overall_risk', risk_metrics)
        
        # Check that risk scores are in valid range
        for metric, value in risk_metrics.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_high_volatility_risk(self):
        """Test risk assessment with high volatility"""
        signal_data = {
            'signal': 'BUY',
            'price': 100,
            'indicators': {
                'atr': 10.0,  # High ATR
                'bb_width': 0.15  # Wide bands
            }
        }
        
        risk_metrics = self.risk_assessor.assess_trade_risk(signal_data)
        
        # Should indicate higher risk
        self.assertGreater(risk_metrics['volatility_risk'], 0.5)
    
    def test_extreme_rsi_risk(self):
        """Test risk assessment with extreme RSI"""
        signal_data = {
            'signal': 'BUY',
            'price': 100,
            'indicators': {
                'rsi': 20  # Oversold
            }
        }
        
        risk_metrics = self.risk_assessor.assess_trade_risk(signal_data)
        
        # Should indicate higher momentum risk
        self.assertGreater(risk_metrics['momentum_risk'], 0.5)
    
    def test_weak_trend_risk(self):
        """Test risk assessment with weak trend"""
        signal_data = {
            'signal': 'BUY',
            'price': 100,
            'indicators': {
                'adx': 15  # Weak trend
            }
        }
        
        risk_metrics = self.risk_assessor.assess_trade_risk(signal_data)
        
        # Weak trend should contribute to overall risk
        self.assertIsNotNone(risk_metrics['overall_risk'])
    
    def test_missing_indicators(self):
        """Test risk assessment with missing indicators"""
        signal_data = {
            'signal': 'BUY',
            'price': 100,
            'indicators': {}
        }
        
        risk_metrics = self.risk_assessor.assess_trade_risk(signal_data)
        
        # Should return default values
        self.assertAlmostEqual(risk_metrics['risk_score'], 0.5, places=1)


class TestMLIntegration(unittest.TestCase):
    """Integration tests for ML components"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not SKLEARN_AVAILABLE:
            self.skipTest("scikit-learn not available")
    
    def test_end_to_end_workflow(self):
        """Test complete workflow: train, predict, filter, assess risk"""
        # Generate training data
        np.random.seed(42)
        training_data = []
        labels = []
        
        for i in range(50):
            signal_data = {
                'signal': 'BUY',
                'price': 100 + np.random.randn() * 5,
                'indicators': {
                    'rsi': 50 + np.random.randn() * 15,
                    'macd': np.random.randn(),
                    'macd_signal': np.random.randn(),
                    'atr': 2.0,
                    'adx': 25
                }
            }
            training_data.append(signal_data)
            labels.append(np.random.randint(0, 2))
        
        # Train model
        ml_filter = MLSignalFilter(model_type='random_forest')
        metrics = ml_filter.train(training_data, labels)
        
        self.assertTrue(ml_filter.is_trained)
        
        # Test prediction
        test_signal = training_data[0]
        confidence, win_prob = ml_filter.predict_signal_quality(test_signal)
        
        self.assertIsNotNone(confidence)
        self.assertIsNotNone(win_prob)
        
        # Test filtering
        should_filter, scores = ml_filter.should_filter_signal(test_signal)
        
        self.assertIsInstance(should_filter, bool)
        
        # Test risk assessment
        risk_assessor = MLRiskAssessor()
        risk_metrics = risk_assessor.assess_trade_risk(test_signal)
        
        self.assertIsNotNone(risk_metrics)
        
        # Verify all components worked
        self.assertGreater(metrics['accuracy'], 0.0)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(win_prob, 1.0)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMLSignalFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestMLRiskAssessor))
    suite.addTests(loader.loadTestsFromTestCase(TestMLIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    
    if not SKLEARN_AVAILABLE:
        print("ERROR: scikit-learn not available")
        print("Install with: pip install scikit-learn")
        sys.exit(1)
    
    success = run_tests()
    sys.exit(0 if success else 1)
