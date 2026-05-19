import streamlit as st
import yfinance as yf
import pandas as pd

# ==========================================
# 系統與版面設定
# ==========================================
st.set_page_config(page_title="股票MACD評估", layout="wide")

# ==========================================
# 初始化 Session State
# ==========================================
if 's1' not in st.session_state: st.session_state.s1 = ""
if 's2' not in st.session_state: st.session_state.s2 = ""
if 's3' not in st.session_state: st.session_state.s3 = ""
if 's4' not in st.session_state: st.session_state.s4 = ""
if 's5' not in st.session_state: st.session_state.s5 = ""

def clear_inputs():
    st.session_state.s1 = ""
    st.session_state.s2 = ""
    st.session_state.s3 = ""
    st.session_state.s4 = ""
    st.session_state.s5 = ""

# ==========================================
# 核心計算與邏輯函式
# ==========================================
def calculate_macd(df):
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = df['EMA12'] - df['EMA26']
    df['MACD'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['DIF'] - df['MACD']
    return df

def check_asu_strategy(stock_id):
    ticker = f"{stock_id}.TW"
    
    try:
        # 🟢 【新增】透過 yfinance 取得股票基本資料與名稱
        ticker_data = yf.Ticker(ticker)
        # 嘗試取得名稱，如果抓不到就給空字串
        stock_name = ticker_data.info.get('shortName', '') 
        
        # 組合顯示標題：如果有抓到名稱，就顯示「2330 (TAIWAN SEMICONDUCTOR)」，沒有就只顯示「2330」
        display_title = f"{stock_id} ({stock_name})" if stock_name else f"{stock_id}"

        # 抓取日、週、月線資料
        df_m = yf.download(ticker, period="2y", interval="1mo", progress=False)
        df_w = yf.download(ticker, period="1y", interval="1wk", progress=False)
        df_d = yf.download(ticker, period="6mo", interval="1d", progress=False)
        
        if df_m.empty or df_w.empty or df_d.empty:
            st.error(f"[{stock_id}] 資料讀取失敗，請確認代號是否正確。")
            return
            
        if isinstance(df_m.columns, pd.MultiIndex):
            df_m.columns = df_m.columns.get_level_values(0)
            df_w.columns = df_w.columns.get_level_values(0)
            df_d.columns = df_d.columns.get_level_values(0)
            
        df_m = calculate_macd(df_m)
        df_w = calculate_macd(df_w)
        
        m_hist_now = df_m['Hist'].iloc[-1]
        m_hist_prev = df_m['Hist'].iloc[-2]
        m_dif_now = df_m['DIF'].iloc[-1]
        
        w_hist_now = df_w['Hist'].iloc[-1]
        w_hist_prev = df_w['Hist'].iloc[-2]
        
        df_d['60MA'] = df_d['Close'].rolling(window=60).mean()
        
        d_close = float(df_d['Close'].iloc[-1])
        d_60ma = float(df_d['60MA'].iloc[-1])
        
        condition_1 = (m_hist_now > 0) and (m_hist_prev <= 0) and (m_dif_now > 0)
        condition_2 = (m_hist_now > 0) and (m_hist_prev > 0) and (w_hist_now > 0) and (w_hist_prev <= 0)
        
        # 🟢 【修改】將原本的 stock_id 替換為包含名稱的 display_title
        with st.expander(f"📊 標的：{display_title} (點擊展開/收合)", expanded=True):
            col1, col2 = st.columns(2)
            col1.metric("目前股價", f"{d_close:.2f}")
            col2.metric("季線 (60MA) 位置", f"{d_60ma:.2f}")
            
            if condition_1:
                st.success("🚨【阿素訊號觸發】月線零軸上第一根紅棒！長線趨勢剛發動！")
            elif condition_2:
                st.warning("⭐【阿素加碼點觸發】月線持續紅棒，週線剛翻紅！適合加碼！")
            else:
                st.info("❌【未達標】目前沒有好型態。")
                if m_hist_now < 0:
                    st.write("- **原因**：月線 MACD 目前還是綠棒。")
                elif m_hist_now > 0 and w_hist_now < 0:
                    st.write("- **原因**：月線雖紅，但週線目前在修正 (綠棒)，繼續耐心等。")
                else:
                    st.write("- **原因**：雖然月週皆紅，但並非「剛翻紅」的起漲點，追高有風險。")

    except Exception as e:
         st.error(f"[{stock_id}] 分析失敗: {e}")

# ==========================================
# 左側側邊欄 (UI 介面)
# ==========================================
with st.sidebar:
    st.header("⚙️ 監控名單設定")
    st.markdown("請在下方輸入您想分析的股票代號：")
    
    stock1 = st.text_input("股票 1", key="s1", placeholder="例如：00878")
    stock2 = st.text_input("股票 2", key="s2", placeholder="例如：00935")
    stock3 = st.text_input("股票 3", key="s3", placeholder="例如：2330")
    stock4 = st.text_input("股票 4", key="s4", placeholder="例如：2382")
    stock5 = st.text_input("股票 5", key="s5", placeholder="例如：1519")
    
    st.divider() 
    
    st.markdown("""
        <style>
        div[data-testid="stButton"] button {
            height: 2.8rem;
            white-space: nowrap; 
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        start_analyze = st.button("✅ 輸入完成", type="primary", use_container_width=True)
    with btn_col2:
        st.button("🔄 重新輸入", on_click=clear_inputs, use_container_width=True)

# ==========================================
# 右側主畫面 (分析結果區)
# ==========================================
st.title("📈 阿素手把手 - 股票自動篩選器")

if start_analyze:
    st.markdown("---")
    
    raw_inputs = [stock1, stock2, stock3, stock4, stock5]
    watch_list = [s.strip() for s in raw_inputs if s.strip()]
    
    if len(watch_list) == 0:
        st.warning("⚠️ 請在左側至少輸入一檔股票代號。")
    else:
        with st.spinner('資料連線計算中，請稍候...'):
            for stock in watch_list:
                check_asu_strategy(stock)
        
        st.divider()
        st.success("結論：沒有好型態就不要買！")
else:
    st.info("👈 請在左側側邊欄輸入股票代號，並點擊「輸入完成」按鈕開始分析。")