# SmartGST AI ERP - Machine Learning Models Guide

## Overview

SmartGST AI ERP includes multiple machine learning models for intelligent business insights and automation.

## Available Models

### 1. Sales Forecasting

**Purpose:** Predict future sales trends

**Technology:** LSTM Neural Network with TensorFlow

**Inputs:**
- Historical sales data
- Seasonal patterns
- Product category
- Time period

**Outputs:**
- Sales forecast for next 7/30/90 days
- Confidence interval
- Trend direction

**Accuracy:** 85-95% (depends on data volume)

**Location:** `ml-models/sales_forecasting/`

**Usage:**
```python
from ml_models.sales_forecasting import SalesForecaster

forecaster = SalesForecaster()
predictions = forecaster.predict(
    product_id=1,
    days_ahead=30,
    branch_id=1
)
```

---

### 2. Demand Prediction

**Purpose:** Forecast product demand

**Technology:** XGBoost with scikit-learn

**Inputs:**
- Historical purchase/sales data
- Inventory levels
- Seasonality
- External factors

**Outputs:**
- Demand quantity
- Recommended stock level
- Reorder point

**Accuracy:** 80-92%

**Location:** `ml-models/demand_prediction/`

**Usage:**
```python
from ml_models.demand_prediction import DemandPredictor

predictor = DemandPredictor()
demand = predictor.predict(
    product_id=1,
    days_ahead=30
)
```

---

### 3. Fraud Detection

**Purpose:** Identify suspicious invoices and transactions

**Technology:** Isolation Forest + Random Forest

**Detection Criteria:**
- Unusual amount
- Duplicate detection
- Seller pattern deviation
- High refund rate
- Multiple failed payments

**Outputs:**
- Fraud probability (0-100%)
- Risk level (low/medium/high)
- Explanation

**Accuracy:** 88-94%

**Location:** `ml-models/fraud_detection/`

**Usage:**
```python
from ml_models.fraud_detection import FraudDetector

detector = FraudDetector()
result = detector.detect(
    invoice_id=1,
    amount=10000,
    customer_id=5,
    branch_id=1
)
```

---

### 4. Customer Segmentation

**Purpose:** Segment customers for targeted actions

**Technology:** K-Means Clustering

**Segmentation Factors:**
- Purchase value (RFM analysis)
- Purchase frequency
- Payment behavior
- Outstanding amount
- Product preferences

**Segments:**
- Premium Customers (High value, frequent)
- Regular Customers (Stable, consistent)
- At-Risk Customers (Decreasing activity)
- New Customers (Low transaction history)

**Location:** `ml-models/customer_segmentation/`

**Usage:**
```python
from ml_models.customer_segmentation import CustomerSegmenter

segmenter = CustomerSegmenter()
segment = segmenter.predict(customer_id=1)
# Output: "premium", "regular", "at_risk", or "new"
```

---

### 5. Invoice OCR & Data Extraction

**Purpose:** Extract structured data from invoice images/PDFs

**Technology:** Pytesseract + OpenCV + NLP

**Extracted Fields:**
- Invoice number
- Date
- Customer name
- Vendor name
- GST number
- Line items (product, quantity, price)
- Tax breakdown (CGST/SGST/IGST)
- Total amount
- Payment terms

**Accuracy:** 85-95% (depends on document quality)

**Location:** `ml-models/ocr_processor/`

**Usage:**
```python
from ml_models.ocr_processor import InvoiceOCR

ocr = InvoiceOCR()
extracted_data = ocr.extract_from_image(
    image_path="invoice.jpg",
    document_type="invoice"
)

# Output:
# {
#     "invoice_number": "INV-2024-001",
#     "date": "2024-01-15",
#     "total_amount": 5000,
#     "cgst": 450,
#     "sgst": 450,
#     "items": [...]
# }
```

---

### 6. Expense Analysis & Categorization

**Purpose:** Categorize expenses automatically

**Technology:** Text Classification with NLP

**Categories:**
- Office Supplies
- Travel
- Utilities
- Marketing
- Maintenance
- Salaries
- Rent
- Transportation
- Other

**Accuracy:** 90%+

**Location:** `ml-models/expense_analysis/`

---

### 7. Product Performance Analysis

**Purpose:** Identify high/low performing products

**Metrics:**
- Sales velocity
- Profit margin
- Stock turnover
- Customer satisfaction
- Trend (increasing/decreasing)

**Location:** `ml-models/product_analysis/`

---

### 8. Business Health Scoring

**Purpose:** Overall business health assessment

**Scoring Factors:**
- Revenue trend
- Profit margin
- Cash flow
- Inventory health
- Customer satisfaction
- Payment timeliness
- GST compliance

**Output:**
- Health Score (0-100)
- Risk Level
- Recommendations

**Location:** `ml-models/business_health/`

---

## Model Training

### Training Data Requirements

**Minimum Data:**
- Sales Forecasting: 100+ historical transactions
- Demand Prediction: 50+ per product
- Fraud Detection: 1000+ transactions
- Customer Segmentation: 50+ customers
- OCR: Pre-trained (uses transfer learning)

**Recommended Data:**
- 1+ year of historical data
- Diverse product/customer base
- Multiple branches

### Training Process

```python
from ml_models.trainer import ModelTrainer

trainer = ModelTrainer()

# Train sales forecasting model
trainer.train_sales_forecasting(
    data_path="historical_data.csv",
    lookback_period=30,
    forecast_horizon=30
)

# Train demand prediction
trainer.train_demand_prediction(
    data_path="historical_data.csv",
    test_size=0.2
)

# Train fraud detection
trainer.train_fraud_detection(
    data_path="transactions.csv",
    fraud_labels="fraud_labels.csv"
)
```

---

## Model Deployment

### API Integration

Models are exposed through REST API:

```bash
# Get sales forecast
GET /api/v1/ml/sales-forecast?product_id=1&days=30

# Get demand prediction
GET /api/v1/ml/demand-prediction?product_id=1

# Check fraud probability
POST /api/v1/ml/fraud-detection
{
    "invoice_id": 1,
    "amount": 5000
}

# Get customer segment
GET /api/v1/ml/customer-segment?customer_id=1

# Extract from invoice
POST /api/v1/ml/ocr-extract
{
    "file": <image_file>
}
```

### Performance Metrics

Endpoints return:
- Prediction/result
- Confidence score
- Explanation
- Timestamp
- Model version

---

## Model Retraining

### Automatic Retraining

Models automatically retrain when:
- New training data accumulated
- Performance metrics drop
- Monthly schedule (configurable)

```python
# Scheduled retraining
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    trainer.retrain_all_models,
    'monthly',
    day=1
)
scheduler.start()
```

### Manual Retraining

```bash
# Via CLI
python ml-models/train.py --model sales_forecasting

# Via API
POST /api/v1/admin/ml/retrain
{
    "model": "sales_forecasting"
}
```

---

## Monitoring Model Performance

### Metrics to Track

```python
from ml_models.monitoring import ModelMonitor

monitor = ModelMonitor()

# Get model performance
performance = monitor.get_metrics(model_name="sales_forecasting")
# {
#     "accuracy": 0.92,
#     "precision": 0.89,
#     "recall": 0.91,
#     "f1_score": 0.90,
#     "mape": 0.08  # Mean Absolute Percentage Error
# }

# Get prediction accuracy
accuracy = monitor.validate_predictions(
    model_name="demand_prediction",
    actual_values=actual,
    predictions=predictions
)
```

### Alert Thresholds

- **Accuracy drops below:** 75% → alert
- **Prediction latency:** > 5 seconds → warning
- **Model age:** > 90 days → retrain

---

## Best Practices

### 1. Data Quality
```python
# Validate input data
if not data.is_valid():
    raise ValueError("Invalid data provided")

# Handle missing values
data.fillna(method='ffill')

# Remove outliers
data = data[data.price < data.price.quantile(0.99)]
```

### 2. Model Validation
```python
# Always validate before deployment
validator = ModelValidator()
if not validator.validate(model):
    raise Exception("Model validation failed")
```

### 3. Fallback Handling
```python
# Provide sensible defaults
try:
    prediction = model.predict(data)
except Exception as e:
    prediction = DEFAULT_FALLBACK_VALUE
    log_error(e)
```

### 4. Performance Tuning
```python
# Batch predictions
predictions = model.predict_batch(data_list)

# Cache results
cache.set(key, prediction, ttl=3600)
```

---

## Configuration

### Model Configuration File

```yaml
# models_config.yaml

sales_forecasting:
  enabled: true
  model_type: lstm
  lookback_period: 30
  forecast_horizon: 30
  batch_size: 32
  epochs: 100

demand_prediction:
  enabled: true
  model_type: xgboost
  test_size: 0.2
  n_estimators: 100

fraud_detection:
  enabled: true
  model_type: isolation_forest
  contamination: 0.1
  random_state: 42

ocr:
  enabled: true
  model_type: tesseract
  confidence_threshold: 0.7
```

---

## Troubleshooting

### Issue: Low Prediction Accuracy

**Solutions:**
1. Add more training data
2. Feature engineering
3. Hyperparameter tuning
4. Try different model architecture
5. Check for data quality issues

### Issue: Model Training Fails

```bash
# Check logs
tail -f logs/training.log

# Validate data
python ml-models/validate_data.py

# Debug
python ml-models/debug.py --model sales_forecasting
```

### Issue: Slow Predictions

```python
# Optimize model
model.optimize()

# Use GPU
model.use_gpu()

# Batch predictions
predictions = model.predict_batch(data)
```

---

## Integration with FastAPI

### Middleware Setup

```python
# app/api/routes/ml.py

from fastapi import APIRouter, BackgroundTasks
from ml_models import SalesForecaster, FraudDetector

router = APIRouter()

@router.get("/sales-forecast")
async def get_sales_forecast(
    product_id: int,
    days: int = 30
):
    forecaster = SalesForecaster()
    prediction = forecaster.predict(product_id, days)
    return prediction

@router.post("/fraud-check")
async def check_fraud(invoice_id: int):
    detector = FraudDetector()
    result = detector.detect(invoice_id)
    return result
```

---

## Future Model Additions

- Customer churn prediction
- Supplier risk assessment
- Price optimization
- Inventory optimization
- Route optimization for deliveries
- Payment default prediction

---

For more information, see [README.md](../README.md) and [DEPLOYMENT.md](./DEPLOYMENT.md).
