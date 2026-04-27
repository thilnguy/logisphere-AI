import os
import pandas as pd
from prophet import Prophet
import warnings

# Suppress cmdstanpy logging which can be noisy
import logging
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

def run_forecast():
    """Reads historical cleaned data, trains Prophet on shipping volume, and forecasts 90 days out."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_file = os.path.join(base_dir, "data", "cleaned", "Logistics_Cleaned.csv")
    output_file = os.path.join(base_dir, "data", "analytics", "Forecast_Prophet.csv")

    try:
        df = pd.read_csv(input_file)
        
        # Ensure date format
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df = df.dropna(subset=["order_date"])

        # Aggregate daily volume
        daily_volume = df.groupby(df["order_date"].dt.date).size().reset_index(name="volume")
        daily_volume.columns = ["ds", "y"]

        # Instantiate and fit Prophet
        model = Prophet(
            daily_seasonality=False,
            yearly_seasonality=True,  # Now enabled with 2 years of history
            weekly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.add_country_holidays(country_name='FR')
        model.fit(daily_volume)

        # Predict next 180 days (6 months tactical horizon)
        future = model.make_future_dataframe(periods=180, freq='D')
        forecast = model.predict(future)

        # Keep relevant columns and ensure no negative volumes
        forecast = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        forecast["yhat"] = forecast["yhat"].clip(lower=0).round()
        forecast["yhat_lower"] = forecast["yhat_lower"].clip(lower=0).round()
        forecast["yhat_upper"] = forecast["yhat_upper"].clip(lower=0).round()

        # Save to analytics
        forecast.to_csv(output_file, index=False)
        print(f"✅ Forecast Agent: 6-month (180 days) tactical prediction generated -> {output_file}")
    
    except Exception as e:
        print(f"❌ Forecast Agent Error: {str(e)}")

if __name__ == "__main__":
    run_forecast()
