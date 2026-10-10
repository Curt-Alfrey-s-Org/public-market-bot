#!/usr/bin/env python3
"""
ML Signal Filter Module for market-pie5-bot
Implements machine learning models for filtering trading signals and improving win rate.

Features:
- Random Forest classifier for signal quality prediction
- Gradient Boosting for trade success probability
- Feature engineering from technical indicators
- Model training, evaluation, and persistence
"""

import os
import pickle
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
import pandas as pd
from collections import OrderedDict

# Try to import scikit-learn
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class MLSignalFilter:
    """
    Machine Learning Signal Filter for trading signal quality assessment
    Uses ensemble methods to predict signal quality and trade success probability
    """
    
    def __init__(self, model_type: str = 'random_forest', model_path: Optional[str] = None):
        """
        Initialize ML Signal Filter
        
        Args:
            model_type: Type of model ('random_forest' or 'gradient_boosting')
            model_path: Path to load pre-trained model (optional)
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available - ML filtering disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
        # Feature importance tracking
        self.feature_importance = {}
        
        # Model performance metrics
        self.metrics = {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'auc': 0.0
        }
        
        # Prediction cache for performance
        self._prediction_cache = {}  # {(symbol, signal, price_hash): (confidence, win_prob)}
        self._cache_timestamp = {}  # Track when cache was created
        self._cache_ttl_seconds = 60  # Cache TTL: 1 minute (signals can change quickly)
        
        # Initialize model
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42
            )
        else:
            logger.error(f"Unknown model type: {model_type}")
            self.enabled = False
            return
        
        # Load pre-trained model if path provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        
        logger.info(f"Initialized MLSignalFilter (type={model_type}, enabled={self.enabled})")
    
    def extract_features(self, signal_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Extract features from signal data for ML prediction
        
        Args:
            signal_data: Dictionary containing:
                - signal: 'BUY', 'SELL', or 'HOLD'
                - price: Current price
                - indicators: Dict of technical indicator values
                - market_conditions: Optional market condition indicators
                
        Returns:
            DataFrame with extracted features or None if extraction fails
        """
        if not self.enabled:
            return None
        
        try:
            features = {}
            
            # Signal type encoding (0=HOLD, 1=BUY, 2=SELL)
            signal_map = {'HOLD': 0, 'BUY': 1, 'SELL': 2}
            features['signal_type'] = signal_map.get(signal_data.get('signal', 'HOLD'), 0)
            
            # Price features
            if 'price' in signal_data:
                features['price'] = signal_data['price']
            
            # Technical indicator features
            indicators = signal_data.get('indicators', {})
            
            # RSI features
            if 'rsi' in indicators:
                features['rsi'] = indicators['rsi']
                features['rsi_oversold'] = 1 if indicators['rsi'] < 30 else 0
                features['rsi_overbought'] = 1 if indicators['rsi'] > 70 else 0
            
            # MACD features
            if 'macd' in indicators and 'macd_signal' in indicators:
                features['macd'] = indicators['macd']
                features['macd_signal'] = indicators['macd_signal']
                features['macd_histogram'] = indicators.get('macd_histogram', 0)
                features['macd_bullish'] = 1 if indicators['macd'] > indicators['macd_signal'] else 0
            
            # Bollinger Bands features
            if all(k in indicators for k in ['bb_upper', 'bb_middle', 'bb_lower']):
                bb_width = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']
                features['bb_width'] = bb_width
                
                if 'price' in signal_data:
                    # Position within bands (0 to 1)
                    bb_range = indicators['bb_upper'] - indicators['bb_lower']
                    if bb_range > 0:
                        features['bb_position'] = (signal_data['price'] - indicators['bb_lower']) / bb_range
                    else:
                        features['bb_position'] = 0.5
            
            # Moving average features
            if 'sma_fast' in indicators and 'sma_slow' in indicators:
                features['sma_fast'] = indicators['sma_fast']
                features['sma_slow'] = indicators['sma_slow']
                features['sma_crossover'] = 1 if indicators['sma_fast'] > indicators['sma_slow'] else 0
            
            # Momentum features
            if 'momentum' in indicators:
                features['momentum'] = indicators['momentum']
                features['momentum_positive'] = 1 if indicators['momentum'] > 0 else 0
            
            # Volatility features
            if 'atr' in indicators:
                features['atr'] = indicators['atr']
            
            if 'adx' in indicators:
                features['adx'] = indicators['adx']
                features['strong_trend'] = 1 if indicators['adx'] > 25 else 0
            
            # Stochastic features
            if 'stoch_k' in indicators:
                features['stoch_k'] = indicators['stoch_k']
                features['stoch_oversold'] = 1 if indicators['stoch_k'] < 20 else 0
                features['stoch_overbought'] = 1 if indicators['stoch_k'] > 80 else 0
            
            # Market condition features
            market_conditions = signal_data.get('market_conditions', {})
            if 'volume' in market_conditions:
                features['volume'] = market_conditions['volume']
            
            if 'volume_ratio' in market_conditions:
                features['volume_ratio'] = market_conditions['volume_ratio']
            
            # Create DataFrame
            df = pd.DataFrame([features])
            
            # Store feature names on first extraction
            if not self.feature_names:
                self.feature_names = list(df.columns)
            
            # Ensure consistent feature order
            for fname in self.feature_names:
                if fname not in df.columns:
                    df[fname] = 0.0
            
            df = df[self.feature_names]
            
            return df
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def train(self, training_data: List[Dict[str, Any]], labels: List[int]) -> Dict[str, float]:
        """
        Train the ML model on historical trading data
        
        Args:
            training_data: List of signal data dictionaries
            labels: List of outcomes (1 = winning trade, 0 = losing trade)
            
        Returns:
            Dictionary with training metrics
        """
        if not self.enabled:
            logger.error("ML filtering not enabled - cannot train")
            return {}
        
        try:
            logger.info(f"Training model on {len(training_data)} samples...")
            
            # Extract features from all training samples
            feature_dfs = []
            valid_labels = []
            
            for i, signal_data in enumerate(training_data):
                features = self.extract_features(signal_data)
                if features is not None:
                    feature_dfs.append(features)
                    valid_labels.append(labels[i])
            
            if not feature_dfs:
                logger.error("No valid features extracted from training data")
                return {}
            
            # Combine all features
            X = pd.concat(feature_dfs, ignore_index=True)
            y = np.array(valid_labels)
            
            logger.info(f"Extracted features shape: {X.shape}")
            logger.info(f"Feature names: {list(X.columns)}")
            
            # Handle missing values
            X = X.fillna(0)
            
            # Split data for training and validation
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
            
            # Calculate metrics
            self.metrics['accuracy'] = accuracy_score(y_test, y_pred)
            self.metrics['precision'] = precision_score(y_test, y_pred, zero_division=0)
            self.metrics['recall'] = recall_score(y_test, y_pred, zero_division=0)
            self.metrics['f1'] = f1_score(y_test, y_pred, zero_division=0)
            self.metrics['auc'] = roc_auc_score(y_test, y_pred_proba)
            
            # Cross-validation score
            cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
            self.metrics['cv_mean'] = cv_scores.mean()
            self.metrics['cv_std'] = cv_scores.std()
            
            # Feature importance
            if hasattr(self.model, 'feature_importances_'):
                importance = self.model.feature_importances_
                self.feature_importance = dict(zip(self.feature_names, importance))
                
                # Log top features
                sorted_features = sorted(
                    self.feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                logger.info("Top 10 important features:")
                for feat, imp in sorted_features:
                    logger.info(f"  {feat}: {imp:.4f}")
            
            self.is_trained = True
            
            logger.info(f"Model training complete:")
            logger.info(f"  Accuracy: {self.metrics['accuracy']:.4f}")
            logger.info(f"  Precision: {self.metrics['precision']:.4f}")
            logger.info(f"  Recall: {self.metrics['recall']:.4f}")
            logger.info(f"  F1 Score: {self.metrics['f1']:.4f}")
            logger.info(f"  AUC: {self.metrics['auc']:.4f}")
            logger.info(f"  CV Mean: {self.metrics['cv_mean']:.4f} (+/- {self.metrics['cv_std']:.4f})")
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {}
    
    def predict_signal_quality(self, signal_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        Predict the quality/probability of success for a trading signal
        
        Uses caching to avoid redundant predictions for similar signals.
        
        Args:
            signal_data: Dictionary containing signal and indicator data
            
        Returns:
            Tuple of (confidence_score, win_probability)
            - confidence_score: 0.0 to 1.0 (model confidence)
            - win_probability: 0.0 to 1.0 (probability of winning trade)
        """
        if not self.enabled or not self.is_trained:
            logger.warning("Model not trained - returning default values")
            return 0.5, 0.5
        
        # Create cache key from signal data (simplified hash)
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            signal = signal_data.get('signal', 'HOLD')
            price = signal_data.get('price', 0.0)
            # Create simple hash from key indicators
            price_hash = int(price * 100)  # Round to 2 decimals for cache key
            cache_key = (symbol, signal, price_hash)
            
            # Check cache
            if cache_key in self._prediction_cache:
                cache_time = self._cache_timestamp.get(cache_key)
                if cache_time:
                    from datetime import datetime
                    age = (datetime.now() - cache_time).total_seconds()
                    if age < self._cache_ttl_seconds:
                        logger.debug(f"Using cached ML prediction for {symbol} (age: {age:.1f}s)")
                        return self._prediction_cache[cache_key]
        except Exception:
            pass  # If caching fails, continue with prediction
        
        try:
            # Extract features
            features = self.extract_features(signal_data)
            if features is None:
                return 0.5, 0.5
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Win probability is the probability of class 1 (winning trade)
            win_probability = probabilities[1]
            
            # Confidence is the maximum probability
            confidence = max(probabilities)
            
            result = (float(confidence), float(win_probability))
            
            # Cache result
            try:
                self._prediction_cache[cache_key] = result
                self._cache_timestamp[cache_key] = datetime.now()
                # Limit cache size to prevent memory issues
                if len(self._prediction_cache) > 1000:
                    # Remove oldest 20% of entries
                    sorted_items = sorted(self._cache_timestamp.items(), key=lambda x: x[1])
                    to_remove = sorted_items[:len(sorted_items) // 5]
                    for key, _ in to_remove:
                        self._prediction_cache.pop(key, None)
                        self._cache_timestamp.pop(key, None)
            except Exception:
                pass  # If caching fails, continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting signal quality: {e}")
            return 0.5, 0.5
    
    def clear_cache(self):
        """Clear prediction cache (useful when model is retrained)"""
        self._prediction_cache.clear()
        self._cache_timestamp.clear()
        logger.debug("ML signal filter cache cleared")
    
    def should_filter_signal(self, signal_data: Dict[str, Any], 
                            min_confidence: float = 0.6,
                            min_win_prob: float = 0.55) -> Tuple[bool, Dict[str, float]]:
        """
        Determine if a signal should be filtered out (rejected)
        
        Args:
            signal_data: Dictionary containing signal and indicator data
            min_confidence: Minimum confidence threshold (default: 0.6)
            min_win_prob: Minimum win probability threshold (default: 0.55)
            
        Returns:
            Tuple of (should_filter, scores)
            - should_filter: True if signal should be rejected
            - scores: Dictionary with confidence and win_probability
        """
        confidence, win_prob = self.predict_signal_quality(signal_data)
        
        scores = {
            'confidence': float(confidence),
            'win_probability': float(win_prob)
        }
        
        # Filter if either confidence or win probability is too low
        # Convert to native Python bool to avoid numpy bool type issues
        should_filter = bool((confidence < min_confidence) or (win_prob < min_win_prob))
        
        if should_filter:
            logger.info(f"Signal filtered: confidence={confidence:.3f}, win_prob={win_prob:.3f}")
        else:
            logger.debug(f"Signal accepted: confidence={confidence:.3f}, win_prob={win_prob:.3f}")
        
        return should_filter, scores
    
    def save_model(self, model_path: str):
        """
        Save trained model to disk
        
        Args:
            model_path: Path to save the model
        """
        if not self.is_trained:
            logger.error("Cannot save untrained model")
            return
        
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'feature_importance': self.feature_importance,
                'metrics': self.metrics,
                'model_type': self.model_type
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self, model_path: str):
        """
        Load trained model from disk
        
        Args:
            model_path: Path to load the model from
        """
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.feature_importance = model_data.get('feature_importance', {})
            self.metrics = model_data.get('metrics', {})
            self.model_type = model_data.get('model_type', 'unknown')
            self.is_trained = True
            
            logger.info(f"Model loaded from {model_path}")
            logger.info(f"  Model type: {self.model_type}")
            logger.info(f"  Accuracy: {self.metrics.get('accuracy', 0):.4f}")
            logger.info(f"  Features: {len(self.feature_names)}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.is_trained = False


class MLRiskAssessor:
    """
    ML-based risk assessment for trading decisions
    Provides additional risk metrics based on market conditions
    """
    
    def __init__(self):
        """Initialize ML Risk Assessor"""
        self.enabled = SKLEARN_AVAILABLE
        logger.info(f"Initialized MLRiskAssessor (enabled={self.enabled})")
    
    def assess_trade_risk(self, signal_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Assess risk level for a potential trade
        
        Args:
            signal_data: Dictionary containing signal and indicator data
            
        Returns:
            Dictionary with risk metrics:
            - risk_score: 0.0 (low risk) to 1.0 (high risk)
            - volatility_risk: Risk from price volatility
            - momentum_risk: Risk from momentum indicators
            - overall_risk: Combined risk assessment
        """
        if not self.enabled:
            return {'risk_score': 0.5, 'volatility_risk': 0.5, 
                   'momentum_risk': 0.5, 'overall_risk': 0.5}
        
        try:
            indicators = signal_data.get('indicators', {})
            risk_factors = []
            
            # Volatility risk (from ATR and Bollinger Bands width)
            volatility_risk = 0.5
            if 'atr' in indicators:
                # Normalize ATR (assuming typical ATR is 1-5% of price)
                atr_norm = min(indicators['atr'] / signal_data.get('price', 100) / 0.05, 1.0)
                volatility_risk = atr_norm
                risk_factors.append(volatility_risk)
            
            if 'bb_width' in indicators:
                # Wide bands = high volatility
                bb_risk = min(indicators['bb_width'] / 0.1, 1.0)  # Normalize to 10% width
                risk_factors.append(bb_risk)
            
            # Momentum risk (extreme RSI or momentum values)
            momentum_risk = 0.5
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                # Risk is high when RSI is at extremes
                if rsi < 30 or rsi > 70:
                    momentum_risk = 0.7
                    risk_factors.append(momentum_risk)
            
            if 'momentum' in indicators:
                # High absolute momentum = higher risk
                mom_abs = abs(indicators['momentum'])
                mom_risk = min(mom_abs / 0.1, 1.0)  # Normalize to 10% momentum
                risk_factors.append(mom_risk)
            
            # Trend strength risk (weak trends are riskier)
            if 'adx' in indicators:
                adx = indicators['adx']
                # Low ADX = weak trend = higher risk
                trend_risk = 1.0 - min(adx / 40, 1.0)  # Normalize to ADX of 40
                risk_factors.append(trend_risk)
            
            # Calculate overall risk
            if risk_factors:
                overall_risk = np.mean(risk_factors)
            else:
                overall_risk = 0.5
            
            return {
                'risk_score': overall_risk,
                'volatility_risk': volatility_risk,
                'momentum_risk': momentum_risk,
                'overall_risk': overall_risk
            }
            
        except Exception as e:
            logger.error(f"Error assessing trade risk: {e}")
            return {'risk_score': 0.5, 'volatility_risk': 0.5,
                   'momentum_risk': 0.5, 'overall_risk': 0.5}


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("ML Signal Filter Module - Example Usage")
    print("="*60)
    print(f"scikit-learn available: {SKLEARN_AVAILABLE}")
    
    if not SKLEARN_AVAILABLE:
        print("\nERROR: scikit-learn not installed")
        print("Install with: pip install scikit-learn")
        exit(1)
    
    # Create sample training data
    print("\n" + "="*60)
    print("Generating Sample Training Data")
    print("="*60)
    
    np.random.seed(42)
    n_samples = 200
    
    training_data = []
    labels = []
    
    for i in range(n_samples):
        # Create synthetic signal data
        signal_data = {
            'signal': np.random.choice(['BUY', 'SELL']),
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
            },
            'market_conditions': {
                'volume': 1000000 + np.random.randint(-200000, 200000),
                'volume_ratio': 0.8 + np.random.randn() * 0.2
            }
        }
        
        # Generate synthetic label (1 = win, 0 = loss)
        # Make it somewhat correlated with RSI for demo purposes
        rsi = signal_data['indicators']['rsi']
        win_prob = 0.7 if (rsi < 35 or rsi > 65) else 0.4
        label = 1 if np.random.rand() < win_prob else 0
        
        training_data.append(signal_data)
        labels.append(label)
    
    print(f"Generated {n_samples} training samples")
    print(f"Win rate: {sum(labels)/len(labels):.2%}")
    
    # Test Random Forest
    print("\n" + "="*60)
    print("Testing Random Forest Classifier")
    print("="*60)
    
    rf_filter = MLSignalFilter(model_type='random_forest')
    metrics = rf_filter.train(training_data, labels)
    
    print("\nTraining Results:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Test prediction on new data
    print("\n" + "="*60)
    print("Testing Signal Prediction")
    print("="*60)
    
    test_signal = {
        'signal': 'BUY',
        'price': 105,
        'indicators': {
            'rsi': 28,  # Oversold
            'macd': 0.5,
            'macd_signal': 0.3,
            'macd_histogram': 0.2,
            'bb_upper': 110,
            'bb_middle': 105,
            'bb_lower': 100,
            'sma_fast': 106,
            'sma_slow': 104,
            'momentum': 0.03,
            'atr': 2.5,
            'adx': 30,
            'stoch_k': 25
        },
        'market_conditions': {
            'volume': 1200000,
            'volume_ratio': 1.1
        }
    }
    
    confidence, win_prob = rf_filter.predict_signal_quality(test_signal)
    print(f"\nTest Signal Prediction:")
    print(f"  Confidence: {confidence:.3f}")
    print(f"  Win Probability: {win_prob:.3f}")
    
    should_filter, scores = rf_filter.should_filter_signal(test_signal)
    print(f"\nShould filter signal: {should_filter}")
    print(f"  Scores: {scores}")
    
    # Test risk assessment
    print("\n" + "="*60)
    print("Testing Risk Assessment")
    print("="*60)
    
    risk_assessor = MLRiskAssessor()
    risk_metrics = risk_assessor.assess_trade_risk(test_signal)
    
    print("\nRisk Assessment:")
    for metric, value in risk_metrics.items():
        print(f"  {metric}: {value:.3f}")
    
    # Test model persistence
    print("\n" + "="*60)
    print("Testing Model Persistence")
    print("="*60)
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
        model_path = tmp.name
    
    try:
        rf_filter.save_model(model_path)
        print(f"Model saved to {model_path}")
        
        # Load model
        rf_filter_loaded = MLSignalFilter(model_type='random_forest', model_path=model_path)
        confidence2, win_prob2 = rf_filter_loaded.predict_signal_quality(test_signal)
        print(f"\nLoaded Model Prediction:")
        print(f"  Confidence: {confidence2:.3f}")
        print(f"  Win Probability: {win_prob2:.3f}")
    finally:
        import os
        if os.path.exists(model_path):
            os.remove(model_path)
    
    print("\n" + "="*60)
    print("ML Signal Filter module initialized successfully")
    print("="*60)
