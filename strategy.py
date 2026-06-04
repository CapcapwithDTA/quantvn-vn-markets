from quantvn import client
client(apikey="IpM-JjkZUtOiQy6MY0KTv-YbtaeVJSWz8y2nMa0Gwu3ix1IpnjOBGcekyDFORTYheMY21ceujMepm4EjtllD3AR2yjmh2EnCvVhv1XhmiN9L2ijiaO6MbzIj2IkWGlXd")
from quantvn.vn.metrics import Backtest_Stock
from quantvn.vn.data import get_stock_hist
from quantvn.vn.metrics import Metrics, Backtest_Derivates
from quantvn.vn.data import get_derivatives_hist
import pandas as pd
import numpy as np


def gen_position(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df['midpoint'] = (df['High'] + df['Low']) / 2
    df['raw_factor'] = (df['midpoint'] - df['Close']) / df['Close']

    window = 20
    rolling_mean = df['raw_factor'].rolling(window=window).mean()
    rolling_std = df['raw_factor'].rolling(window=window).std()
    df['zscore'] = (df['raw_factor'] - rolling_mean) / (rolling_std + 1e-9) 

    # --- Logic chiến lược giao dịch ---
    df["position"] = 0
    
    # Mua 1000 cổ phiếu khi quá bán (Z-score > 1.5)
    df.loc[df["zscore"] > 1.5, "position"] = 1000  
    # Bán hết khi quá mua (Z-score < -1.0)
    df.loc[df["zscore"] < -1.0, "position"] = 0    
    
    # Fill forward để giữ nguyên trạng thái nếu không có tín hiệu mới
    df["position"] = df["position"].ffill().fillna(0)
    
    # Fix lỗi thời gian cho khung 1D nếu cần
    if 'time' not in df.columns:
        df['time'] = "00:00:00"
        
    return df

# ==========================================
df_raw = get_stock_hist("FPT", resolution="1H")

# Chạy qua hàm tạo position
df_ready = gen_position(df_raw)

# Loại bỏ dòng NaN
df_ready = df_ready.dropna().reset_index(drop=True)

# Đưa vào Backtest
backtest = Backtest_Stock(df_ready, pnl_type="after_fees")
metrics = Metrics(backtest)

print(f"Tỷ lệ thắng (Win Rate): {metrics.win_rate()*100:.2f}%")
print(f"Lợi nhuận ròng PnL: {backtest.PNL().iloc[-1]:,.0f} VND")
print(f"Max Drawdown: {metrics.max_drawdown()*100:.2f}%")

backtest.plot_PNL("FPT - Z-Score Strategy")