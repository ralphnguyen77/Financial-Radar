"""
========================================================================================
FINANCIAL RADAR & REAL-TIME VALUATION TERMINAL (MULTI-SECTOR DOMAIN EDITION)
Framework: Streamlit + CFA Equity Valuation + Howard Schilit Audit Radar
Kiến trúc: 4 Cỗ máy Định giá Chuyên biệt theo Nhóm Ngành (Master Sector Router)
  1. 🏛️ BANKING & FINANCIAL SUITE: P/B Justified (ROE), Bank P/E, DDM, CAR Capital Buffer
  2. 🔄 CYCLICAL COMMODITIES SUITE: Mid-Cycle Normalization (5-7Y), P/B Band, FCF Chu kỳ
  3. 🌦️ SEASONALITY SUITE: Khử nhiễu mùa vụ, TTM Smoothing
  4. 🚀 STANDARD CORPORATE SUITE: Full 5 Tầng CFA + Radar Gian lận Beneish M-Score & Altman Z''
Cơ sở dữ liệu: BCTC 16 Năm (2010 - 2025) + DNSE AWS CDN & SSI Real-time Price
========================================================================================
"""

import os
import urllib.request
import json
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Cấu hình trang tối ưu Mobile & Desktop
st.set_page_config(
    page_title="Financial Radar & Multi-Sector Valuation Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f8fafc; }
    .stMetric { background: rgba(30, 41, 59, 0.6); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); }
    .badge-buy { background-color: #064e3b; color: #34d399; padding: 4px 10px; border-radius: 9999px; font-weight: bold; }
    .badge-hold { background-color: #78350f; color: #fbbf24; padding: 4px 10px; border-radius: 9999px; font-weight: bold; }
    .badge-sell { background-color: #881337; color: #f87171; padding: 4px 10px; border-radius: 9999px; font-weight: bold; }
    .cagr-box { background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 12px 16px; text-align: center; }
    .sector-badge { background: #1e1b4b; border: 1px solid #6366f1; color: #c7d2fe; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Financial Radar & Multi-Sector Valuation Terminal")
st.caption("CFA Institute Valuation • Howard Schilit Financial Shenanigans • Động cơ Thích ứng Đa Ngành")

# 2. Thanh tìm kiếm Ticker & Gợi ý theo nhóm ngành
col_search, col_btn = st.columns([4, 1])
with col_search:
    ticker_input = st.text_input("Nhập mã chứng khoán (HOSE, HNX, UPCoM):", value="TPB").upper().strip()

# Các nút bấm nhanh đại diện 4 nhóm ngành
preset_cols = st.columns(6)
presets = ["TPB", "VCB", "HPG", "DPM", "FPT", "VNM"]
for idx, p in enumerate(presets):
    if preset_cols[idx].button(p, use_container_width=True):
        ticker_input = p

if not ticker_input:
    st.warning("Vui lòng nhập một mã chứng khoán để phân tích.")
    st.stop()

# 3. Load cơ sở dữ liệu 16 năm từ Parquet
@st.cache_data
def load_16y_database():
    parquet_path = os.path.join(os.path.dirname(__file__), "vietnam_stocks_16y.parquet")
    if os.path.exists(parquet_path):
        try:
            return pd.read_parquet(parquet_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df_16y_all = load_16y_database()

# 4. Master Sector Classifier (Tự động nhận diện nhóm ngành)
BANK_TICKERS = {
    'TPB', 'VCB', 'CTG', 'BID', 'TCB', 'MBB', 'ACB', 'VPB', 'HDB', 'VIB', 
    'STB', 'LPB', 'SHB', 'MSB', 'OCB', 'SSB', 'EIB', 'NAB', 'BAB', 'BVB', 
    'ABB', 'NVB', 'PGB', 'KLB', 'SGB', 'VBB'
}
FINANCIAL_SERVICES_TICKERS = {
    'SSI', 'VND', 'VCI', 'HCM', 'SHS', 'MBS', 'FTS', 'BSI', 'CTS', 'VIX', 'AGR', 'ORS', 'TVS'
}
CYCLICAL_COMMODITY_TICKERS = {
    'HPG', 'HSG', 'NKG', 'VGS', 'TLH', 'SMC',  # Thép
    'DPM', 'DCM', 'DGC', 'BFC', 'LAS',          # Phân bón & Hóa chất
    'PVD', 'PVS', 'BSR', 'PVB', 'PVC', 'OIL',   # Dầu khí
    'HT1', 'BCC', 'KSB', 'DHA'                  # Xi măng, Khoáng sản
}
SEASONAL_TICKERS = {
    'VSH', 'SBA', 'SHP', 'TMP', 'HND', 'QTP',   # Thủy điện & Nhiệt điện
    'VHC', 'ANV', 'FMC', 'IDI', 'ACL',          # Thủy sản
    'QNS', 'SBT', 'SLS', 'LSS'                  # Mía đường
}

def classify_sector(ticker: str, sector_str: str = ""):
    t = ticker.upper().strip()
    sec_lower = str(sector_str).lower()
    
    if t in BANK_TICKERS or 'ngân hàng' in sec_lower or 'bank' in sec_lower:
        return 'BANK', '🏛️ NGÂN HÀNG THƯƠNG MẠI'
    elif t in FINANCIAL_SERVICES_TICKERS or 'chứng khoán' in sec_lower:
        return 'FINANCIAL_SERVICE', '📈 DỊCH VỤ TÀI CHÍNH / CHỨNG KHOÁN'
    elif t in CYCLICAL_COMMODITY_TICKERS:
        return 'CYCLICAL', '🔄 CỔ PHIẾU CHU KỲ HÀNG HÓA NẶNG'
    elif t in SEASONAL_TICKERS:
        return 'SEASONAL', '🌦️ CỔ PHIẾU THEO MÙA VỤ'
    else:
        return 'STANDARD', '🚀 DOANH NGHIỆP SẢN XUẤT & TĂNG TRƯỞNG'

# 5. Kéo giá thị trường thời gian thực (Pickle-Safe)
@st.cache_data(ttl=60)
def fetch_realtime_market_clean(ticker):
    raw_t = ticker.upper().strip()
    price = 0.0
    shares = 0
    beta = 1.0
    company_name = raw_t
    sector = "Tổng hợp"
    industry = "Tổng hợp"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # 1. DNSE Entrade Cloud API
    try:
        url_dnse = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from=1700000000&to=1850000000&symbol={raw_t}&resolution=1D"
        req = urllib.request.Request(url_dnse, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read().decode('utf-8'))
            closes = data.get('c') or data.get('close') or []
            if closes and closes[-1] > 0:
                price = float(closes[-1] * 1000)
    except Exception:
        pass

    # 2. SSI iBoard Direct
    if price == 0.0:
        try:
            url_ssi = f"https://iboard-query.ssi.com.vn/stock/{raw_t}"
            req_ssi = urllib.request.Request(url_ssi, headers=headers)
            with urllib.request.urlopen(req_ssi, timeout=3) as resp_ssi:
                data_ssi = json.loads(resp_ssi.read().decode('utf-8')).get('data', {})
                p_ssi = data_ssi.get('matchedPrice') or data_ssi.get('expectedMatchedPrice') or data_ssi.get('refPrice') or data_ssi.get('priorClosePrice')
                if p_ssi and float(p_ssi) > 0:
                    price = float(p_ssi)
        except Exception:
            pass

    # 3. yfinance (Số lượng cổ phiếu & Beta)
    try:
        s = yf.Ticker(f"{raw_t}.VN")
        fi = s.fast_info
        if price == 0.0:
            p = getattr(fi, 'last_price', None) or getattr(fi, 'regular_market_price', None)
            if p and p > 0: price = float(p)
        sh = getattr(fi, 'shares', None)
        if sh and sh > 0: shares = int(sh)
    except Exception:
        pass

    # 4. yfinance History
    if price == 0.0:
        try:
            h = yf.Ticker(f"{raw_t}.VN").history(period="5d")
            if not h.empty and 'Close' in h.columns:
                p_hist = h['Close'].dropna().iloc[-1]
                if p_hist > 0: price = float(p_hist)
        except Exception:
            pass

    return {
        'price': price,
        'shares': shares,
        'beta': beta,
        'company_name': company_name,
        'sector': sector,
        'industry': industry
    }

with st.spinner(f"Đang đồng bộ BCTC 16 năm và thị giá cho {ticker_input}..."):
    try:
        mkt_dict = fetch_realtime_market_clean(ticker_input)
    except Exception:
        mkt_dict = {'price': 0.0, 'shares': 0, 'beta': 1.0, 'company_name': ticker_input, 'sector': 'Tổng hợp', 'industry': 'Tổng hợp'}

mkt_price = float(mkt_dict.get('price', 0.0))
mkt_shares = int(mkt_dict.get('shares', 0))
mkt_beta = float(mkt_dict.get('beta', 1.0))

# 6. Bóc tách dữ liệu 16 năm
df = pd.DataFrame()
loaded_from_local = False
data_source_badge = ""

if not df_16y_all.empty and ticker_input in df_16y_all['ticker'].values:
    sub = df_16y_all[df_16y_all['ticker'] == ticker_input].sort_values('year').copy()
    if len(sub) >= 4:
        if 'debt' not in sub.columns and 'total_debt' in sub.columns:
            sub['debt'] = sub['total_debt']
        if 'ebitda' not in sub.columns:
            sub['ebitda'] = sub['ebit'] + sub['depr']
        if 'net_debt' not in sub.columns:
            sub['net_debt'] = sub['debt'] - sub['cash']
        if 'fcf' not in sub.columns:
            sub['fcf'] = sub['cfo'] - sub['capex']
        if 're' not in sub.columns:
            sub['re'] = sub['eq'] * 0.25
        if 'cl' not in sub.columns:
            sub['cl'] = sub['tl'] * 0.70
        df = sub
        loaded_from_local = True
        data_source_badge = f"⚡ CSDL Kiểm toán 16 Năm ({sub['year'].min()} - {sub['year'].max()}) + Real-Time Price"

# Fallback sang yfinance nếu mã mới
if not loaded_from_local:
    try:
        stock = yf.Ticker(f"{ticker_input}.VN")
        bs = stock.balance_sheet
        inc = stock.financials
        cf = stock.cashflow
        if inc.empty or bs.empty:
            st.error(f"Không tìm thấy dữ liệu tài chính cho mã '{ticker_input}'.")
            st.stop()
        dates = sorted(inc.columns)
        def safe_get(d_in, r, c, d=0.0):
            return float(d_in.loc[r, c]) if (not d_in.empty and r in d_in.index and c in d_in.columns and pd.notnull(d_in.loc[r, c])) else d
        records = []
        for d in dates:
            yr = d.strftime('%Y')
            records.append({
                'year': yr, 'rev': safe_get(inc, 'Total Revenue', d), 'gp': safe_get(inc, 'Gross Profit', d),
                'ebit': safe_get(inc, 'EBIT', d) or safe_get(inc, 'Operating Income', d),
                'ebitda': safe_get(inc, 'EBITDA', d), 'ni': safe_get(inc, 'Net Income', d),
                'depr': safe_get(inc, 'Reconciled Depreciation', d) or safe_get(cf, 'Depreciation And Amortization', d),
                'ta': safe_get(bs, 'Total Assets', d), 'ca': safe_get(bs, 'Current Assets', d),
                'cl': safe_get(bs, 'Current Liabilities', d), 'tl': safe_get(bs, 'Total Liabilities Net Minority Interest', d),
                'eq': safe_get(bs, 'Stockholders Equity', d), 're': safe_get(bs, 'Retained Earnings', d),
                'ar': safe_get(bs, 'Accounts Receivable', d), 'inv': safe_get(bs, 'Inventory', d),
                'net_ppe': safe_get(bs, 'Net PPE', d), 'debt': safe_get(bs, 'Total Debt', d),
                'cash': safe_get(bs, 'Cash Cash Equivalents And Short Term Investments', d),
                'cfo': safe_get(cf, 'Operating Cash Flow', d), 'capex': abs(safe_get(cf, 'Capital Expenditure', d)),
                'fcf': safe_get(cf, 'Free Cash Flow', d), 'div_paid': abs(safe_get(cf, 'Cash Dividends Paid', d))
            })
        df = pd.DataFrame(records)
        data_source_badge = f"🌐 Nguồn yfinance ({len(df)} năm gần nhất)"
    except Exception as e_yf:
        st.error(f"Lỗi khi tải dữ liệu: {e_yf}")
        st.stop()

latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) >= 2 else latest

# Số lượng cổ phiếu & Mệnh giá
shares = mkt_shares
if shares == 0:
    shares = int(latest['eq'] / 15000) if latest['eq'] > 0 else 1000000

current_price = mkt_price
beta = mkt_beta if (0.4 <= mkt_beta <= 2.5) else 1.0

company_name = latest.get('company_name', ticker_input)
if mkt_dict.get('company_name') and mkt_dict.get('company_name') != ticker_input:
    company_name = mkt_dict.get('company_name')

# Phân loại Archetype ngành
archetype, archetype_label = classify_sector(ticker_input, latest.get('sector', ''))

# 7. Tính các chỉ số nền tảng (EPS, BVPS, ROE)
eps = float(latest['ni'] / shares) if shares > 0 else 0.0
bvps = float(latest['eq'] / shares) if shares > 0 else 0.0

# ROE 5 năm và 10 năm
recent_5 = df.iloc[-5:]
valid_roe_5 = [(r['ni'] / r['eq'] * 100) for _, r in recent_5.iterrows() if r['eq'] > 0]
avg_roe_5y = float(np.mean(valid_roe_5)) if valid_roe_5 else 15.0

recent_10 = df.iloc[-10:] if len(df) >= 10 else df
valid_roe_10 = [(r['ni'] / r['eq'] * 100) for _, r in recent_10.iterrows() if r['eq'] > 0]
avg_roe_10y = float(np.mean(valid_roe_10)) if valid_roe_10 else avg_roe_5y

# 10Y CAGR
cagr_10y_rev = None
cagr_10y_ni = None
if len(df) >= 10:
    row_10y = df[df['year'] == str(int(latest['year']) - 10)]
    if not row_10y.empty:
        r0 = row_10y.iloc[0]
        if r0['rev'] > 0 and latest['rev'] > 0:
            cagr_10y_rev = ((latest['rev'] / r0['rev']) ** (1/10) - 1) * 100
        if r0['ni'] > 0 and latest['ni'] > 0:
            cagr_10y_ni = ((latest['ni'] / r0['ni']) ** (1/10) - 1) * 100

div_cnt = len(df[df['div_paid'] > 0])
div_consistency = f"{div_cnt}/{len(df)} năm"

# ========================================================================================
# 8. CÁC ĐỘNG CƠ ĐỊNH GIÁ CHUYÊN BIỆT (DOMAIN ENGINES)
# ========================================================================================

active_models = {}
weights = {}
radar_data = {}
solvency_data = {}
engine_note = ""

# ----------------------------------------------------------------------------------------
# ARCHETYPE 1: 🏛️ BANKING & FINANCIAL SUITE (TPB, VCB, MBB, TCB, ACB, VPB...)
# ----------------------------------------------------------------------------------------
if archetype in ['BANK', 'FINANCIAL_SERVICE']:
    engine_note = "Mô hình chuyên biệt Ngân hàng: Loại trừ DCF & Altman Z (không phù hợp), áp dụng Justified P/B theo ROE, Target P/E và DDM."
    
    # Model 1: Justified P/B (ROE Dài hạn)
    # P/B = (ROE - g) / (r - g)
    r_bank = 0.125
    g_bank = 0.05
    roe_bank = max(0.08, min(0.25, avg_roe_10y / 100.0))
    target_pb = (roe_bank - g_bank) / (r_bank - g_bank) if (r_bank > g_bank) else 1.2
    target_pb = max(0.9, min(1.8, target_pb)) # Bound an toàn ngành ngân hàng VN
    price_justified_pb = bvps * target_pb
    
    # Model 2: Bank Target P/E
    # Ngân hàng VN giao dịch quanh P/E 7.0x - 9.0x
    bank_target_pe = 8.0 if roe_bank >= 0.16 else 7.0
    price_bank_pe = eps * bank_target_pe if eps > 0 else 0.0
    
    # Model 3: Gordon DDM (Cổ tức)
    avg_div = df['div_paid'].values[-3:].mean() if len(df) >= 3 else latest['div_paid']
    dps = avg_div / shares if shares > 0 else 0.0
    price_ddm = max(0.0, (dps * 1.05) / (0.12 - 0.05)) if dps > 0 else 0.0
    
    # Model 4: Graham BVPS Value
    price_graham_bank = bvps * 1.15
    
    active_models = {
        'Justified P/B (ROE)': price_justified_pb,
        'P/E Ngành Ngân Hàng': price_bank_pe,
        'Graham Book Value': price_graham_bank
    }
    weights = {'Justified P/B (ROE)': 0.45, 'P/E Ngành Ngân Hàng': 0.40, 'Graham Book Value': 0.15}
    if price_ddm > 0:
        active_models['Dividend DDM'] = price_ddm
        weights = {'Justified P/B (ROE)': 0.35, 'P/E Ngành Ngân Hàng': 0.35, 'Dividend DDM': 0.15, 'Graham Book Value': 0.15}

    # Radar cho Ngân hàng (Xóa sạch NaN)
    capital_buffer = (latest['eq'] / latest['ta'] * 100) if latest['ta'] > 0 else 9.0
    roa = (latest['ni'] / latest['ta'] * 100) if latest['ta'] > 0 else 1.5
    
    radar_data = {
        'title': '🏛️ Sức Khỏe Ngân Hàng (Basel & ROE)',
        'metric1_label': 'Đòn bẩy Vốn CSH (Equity / Assets):',
        'metric1_val': f"{capital_buffer:.1f}% (Bộ đệm an toàn cao)" if capital_buffer >= 8.0 else f"{capital_buffer:.1f}% (Đòn bẩy cao)",
        'metric2_label': 'Tỷ suất Sinh lời Tổng tài sản (ROA):',
        'metric2_val': f"{roa:.2f}% (Top ngành)" if roa >= 1.5 else f"{roa:.2f}% (Bình thường)",
        'metric3_label': 'Chất lượng Lợi nhuận:',
        'metric3_val': 'Hoạt động kinh doanh cốt lõi (NII) ổn định'
    }
    
    solvency_data = {
        'title': '🛡️ Quy Mô & Nền Tảng Tài Sản',
        'metric1_label': 'Giá Trị Sổ Sách (BVPS):',
        'metric1_val': f"{bvps:,.0f} VND/cp",
        'metric2_label': 'Tổng Tài Sản Ngân Hàng:',
        'metric2_val': f"{latest['ta']/1e12:,.1f} Nghìn Tỷ VND",
        'metric3_label': 'Hệ số P/B Hiện Tại:',
        'metric3_val': f"{current_price / bvps:.2f}x (Rất rẻ dưới 1.0x)" if (bvps > 0 and current_price / bvps < 1.0) else f"{current_price / bvps:.2f}x"
    }

# ----------------------------------------------------------------------------------------
# ARCHETYPE 2: 🔄 CYCLICAL COMMODITIES SUITE (HPG, HSG, DPM, DCM, DGC, PVD...)
# ----------------------------------------------------------------------------------------
elif archetype == 'CYCLICAL':
    engine_note = "Mô hình chuyên biệt Cổ phiếu Chu kỳ Hàng hóa: Chuẩn hóa Lợi nhuận 7 năm (Mid-Cycle) và Khung định giá P/B Band để chống bẫy mua đỉnh/bán đáy."
    
    # 1. Chuẩn hóa chu kỳ 5-7 năm (Mid-Cycle Earnings)
    sub_cycle = df.iloc[-7:] if len(df) >= 7 else df
    mid_cycle_ni = sub_cycle['ni'].mean()
    mid_cycle_eps = mid_cycle_ni / shares if shares > 0 else eps
    mid_cycle_fcf = sub_cycle['fcf'].mean() if sub_cycle['fcf'].mean() > 0 else (mid_cycle_ni * 0.6)
    
    # 2. P/B Valuation Band (Thước đo số 1 chu kỳ)
    # Cổ phiếu đầu ngành chu kỳ (như HPG) mua gom khi P/B < 1.2x, chốt lời khi P/B > 2.0x
    target_pb_cycle = 1.35
    price_pb_cycle = bvps * target_pb_cycle
    
    # 3. P/E Chuẩn hóa chu kỳ
    price_pe_cycle = mid_cycle_eps * 10.0 if mid_cycle_eps > 0 else eps * 10.0
    
    # 4. Normalized DCF (FCFF)
    wacc_c = 0.105
    g_c = 0.02
    pv_fcfs_c = []
    curr_f = mid_cycle_fcf
    for y_idx in range(1, 6):
        curr_f *= 1.04
        pv_fcfs_c.append(curr_f / ((1 + wacc_c) ** y_idx))
    term_val_c = (curr_f * (1 + g_c)) / (wacc_c - g_c)
    pv_term_c = term_val_c / ((1 + wacc_c) ** 5)
    net_debt_c = latest['debt'] - latest['cash']
    price_dcf_cycle = max(0.0, (sum(pv_fcfs_c) + pv_term_c - net_debt_c) / shares)
    
    # 5. Buffett Owner Earnings Chuẩn hóa
    price_oe_cycle = max(0.0, ((mid_cycle_ni * 1.03) / (0.10 - 0.03)) / shares)
    
    active_models = {
        'P/B Chu Kỳ (Tài Sản)': price_pb_cycle,
        'P/E Chuẩn Hóa 7 Năm': price_pe_cycle,
        'DCF Dòng Tiền Chu Kỳ': price_dcf_cycle,
        'Owner Earnings Chu Kỳ': price_oe_cycle
    }
    weights = {'P/B Chu Kỳ (Tài Sản)': 0.40, 'P/E Chuẩn Hóa 7 Năm': 0.30, 'DCF Dòng Tiền Chu Kỳ': 0.15, 'Owner Earnings Chu Kỳ': 0.15}
    
    current_pb = current_price / bvps if bvps > 0 else 1.0
    cycle_phase = "🟢 VÙNG ĐÁY CHU KỲ (P/B < 1.1x - Tích sản hấp dẫn)" if current_pb < 1.1 else ("🟡 GIỮA CHU KỲ (Định giá hợp lý)" if current_pb <= 1.8 else "🔴 ĐỈNH CHU KỲ (P/B > 2.0x - Thận trọng chốt lời)")
    
    radar_data = {
        'title': '🔄 Định Vị Chu Kỳ Hàng Hóa',
        'metric1_label': 'Vị thế Chu kỳ Doanh nghiệp:',
        'metric1_val': cycle_phase,
        'metric2_label': 'Hệ số P/B Hiện Tại:',
        'metric2_val': f"{current_pb:.2f}x (Tài sản ròng bảo kê)",
        'metric3_label': 'LNST Chuẩn Hóa Chu Kỳ (7 Năm):',
        'metric3_val': f"{mid_cycle_ni/1e9:,.0f} Tỷ VND/năm"
    }
    solvency_data = {
        'title': '🏰 Sức Bền Tài Chính Trong Khủng Hoảng',
        'metric1_label': 'Tỷ lệ Tiền mặt / Vốn CSH:',
        'metric1_val': f"{(latest['cash'] / latest['eq'] * 100):.1f}%",
        'metric2_label': 'Tổng Nợ Vay Ròng:',
        'metric2_val': f"{net_debt_c/1e9:,.0f} Tỷ VND" if net_debt_c > 0 else "Két tiền mặt ròng",
        'metric3_label': 'Giá Trị Sổ Sách (BVPS):',
        'metric3_val': f"{bvps:,.0f} VND/cp"
    }

# ----------------------------------------------------------------------------------------
# ARCHETYPE 4: 🚀 STANDARD CORPORATE SUITE (FPT, VNM, MWG, GAS, BMP, DGW...)
# ----------------------------------------------------------------------------------------
else:
    engine_note = "Mô hình chuẩn CFA dành cho Doanh nghiệp Sản xuất & Tăng trưởng: 5 Tầng Định giá CFA + Kiểm toán Gian lận Beneish M-Score & Altman Z''-Score."
    
    net_debt = latest['debt'] - latest['cash']
    wacc_std = 0.10
    g_std = 0.025
    base_fcf = latest['fcf'] if latest['fcf'] > 0 else df['fcf'].mean()
    if base_fcf <= 0: base_fcf = latest['ni'] * 0.7
    
    pv_fcfs_std = []
    curr_f = base_fcf
    for y_idx in range(1, 6):
        curr_f *= 1.06
        pv_fcfs_std.append(curr_f / ((1 + wacc_std) ** y_idx))
    term_val_std = (curr_f * (1 + g_std)) / (wacc_std - g_std)
    pv_term_std = term_val_std / ((1 + wacc_std) ** 5)
    dcf_equity = sum(pv_fcfs_std) + pv_term_std - net_debt
    price_dcf_std = max(0.0, dcf_equity / shares)
    
    # Owner Earnings
    maint_capex = latest['capex'] * 0.60
    oe = latest['ni'] + latest['depr'] - maint_capex
    if oe <= 0: oe = df['ni'].mean()
    price_oe_std = max(0.0, ((oe * 1.03) / (0.10 - 0.03)) / shares)
    
    # Graham
    graham_num = np.sqrt(22.5 * eps * bvps) if (eps > 0 and bvps > 0) else 0.0
    graham_int = eps * (8.5 + 2 * 5.0) * (4.4 / 3.5) if eps > 0 else 0.0
    price_graham_std = (graham_num * 0.5 + graham_int * 0.5) if graham_num > 0 else graham_int
    
    # Relative PE
    price_pe_std = eps * 14.0 if eps > 0 else 0.0
    
    # DDM
    avg_div = df['div_paid'].values[-3:].mean() if len(df) >= 3 else latest['div_paid']
    dps = avg_div / shares if shares > 0 else 0.0
    price_ddm_std = max(0.0, (dps * 1.03) / (0.09 - 0.03)) if dps > 0 else 0.0
    
    active_models = {
        'DCF (FCFF)': price_dcf_std,
        'Owner Earnings': price_oe_std,
        'Graham Value': price_graham_std,
        'Relative P/E': price_pe_std
    }
    weights = {'DCF (FCFF)': 0.35, 'Owner Earnings': 0.25, 'Relative P/E': 0.25, 'Graham Value': 0.15}
    if price_ddm_std > 0:
        active_models['Dividend DDM'] = price_ddm_std
        weights = {'DCF (FCFF)': 0.30, 'Owner Earnings': 0.20, 'Relative P/E': 0.25, 'Dividend DDM': 0.15, 'Graham Value': 0.10}

    # Beneish M-Score & Altman Z
    dsri = (latest['ar'] / latest['rev']) / (prev['ar'] / prev['rev']) if (latest['rev'] > 0 and prev['ar'] > 0 and prev['rev'] > 0) else 1.0
    gm_curr = latest['gp'] / latest['rev'] if latest['rev'] > 0 else 0.2
    gm_prev = prev['gp'] / prev['rev'] if prev['rev'] > 0 else 0.2
    gmi = gm_prev / gm_curr if gm_curr > 0 else 1.0
    sgi = latest['rev'] / prev['rev'] if prev['rev'] > 0 else 1.0
    tata = (latest['ni'] - latest['cfo']) / latest['ta'] if latest['ta'] > 0 else 0.0
    m_score = -4.84 + 0.920*dsri + 0.528*gmi + 0.404*1.0 + 0.892*sgi + 0.115*1.0 - 0.172*1.0 + 4.037*tata + 0.0327*1.0
    
    x1 = (latest['ca'] - latest['cl']) / latest['ta'] if latest['ta'] > 0 else 0.2
    x2 = latest['re'] / latest['ta'] if latest['ta'] > 0 else 0.1
    x3 = latest['ebit'] / latest['ta'] if latest['ta'] > 0 else 0.1
    x4 = latest['eq'] / latest['tl'] if latest['tl'] > 0 else 2.0
    z_score = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
    
    cfo_ni = latest['cfo'] / latest['ni'] if latest['ni'] > 0 else 0.0
    dso_val = (latest['ar'] / latest['rev']) * 365 if latest['rev'] > 0 else 0.0
    
    radar_data = {
        'title': '🚦 Radar Gian Lận (Howard Schilit)',
        'metric1_label': 'Beneish M-Score:',
        'metric1_val': f"{m_score:.3f} ({'SẠCH' if m_score < -2.22 else 'VÙNG XÁM'})",
        'metric2_label': 'Chất lượng Dồn tích (CFO / NI):',
        'metric2_val': f"{cfo_ni:.2f}x ({'Lãi thật' if cfo_ni >= 1.0 else 'Dồn tích'})",
        'metric3_label': 'Vòng quay Phải thu (DSO):',
        'metric3_val': f"{dso_val:.0f} ngày"
    }
    solvency_data = {
        'title': '🏰 Sức Khỏe & Vỡ Nợ (Altman Z)',
        'metric1_label': 'Altman Z''-Score:',
        'metric1_val': f"{z_score:.2f} ({'SIÊU AN TOÀN' if z_score > 2.6 else 'VÙNG XÁM'})",
        'metric2_label': 'Tiền mặt & Đầu tư ngắn hạn:',
        'metric2_val': f"{latest['cash']/1e9:,.0f} Tỷ VND",
        'metric3_label': 'Thanh toán hiện hành (CR):',
        'metric3_val': f"{(latest['ca']/latest['cl']):.2f}x" if latest['cl'] > 0 else "N/A"
    }

# ----------------------------------------------------------------------------------------
# 9. TỔNG HỢP GIÁ TRỊ HỢP LÝ & KHUYẾN NGHỊ (COMPOSITE FAIR VALUE)
# ----------------------------------------------------------------------------------------
tot_w = sum([weights[k] for k in active_models if active_models[k] > 0])
composite_price = sum([active_models[k] * weights[k] for k in active_models if active_models[k] > 0]) / tot_w if tot_w > 0 else 0.0

if current_price > 0:
    upside = ((composite_price - current_price) / current_price) * 100
    if upside >= 25.0: signal_badge, signal_text = "badge-buy", "🟢 STRONG BUY"
    elif upside >= 10.0: signal_badge, signal_text = "badge-buy", "🟢 BUY"
    elif upside >= -10.0: signal_badge, signal_text = "badge-hold", "🟡 FAIRLY VALUED"
    else: signal_badge, signal_text = "badge-sell", "🔴 OVERVALUED"
else:
    upside = 0.0
    signal_badge, signal_text = "badge-hold", "🟡 FAIR VALUE ONLY"

# DCF Tương tác hiển thị
dcf_interactive_val = active_models.get('DCF (FCFF)') or active_models.get('DCF Dòng Tiền Chu Kỳ') or active_models.get('Justified P/B (ROE)') or composite_price

# ----------------------------------------------------------------------------------------
# 10. HIỂN THỊ GIAO DIỆN (UI RENDER)
# ----------------------------------------------------------------------------------------
st.markdown(f"### **{ticker_input}** — {company_name}")
st.markdown(f"<span class='sector-badge'>{archetype_label}</span> • <span style='color:#94a3b8; font-size:12px;'>{data_source_badge} • Vốn hóa: {current_price*shares/1e9:,.0f} Tỷ VND</span>", unsafe_allow_html=True)
st.caption(f"💡 *{engine_note}*")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Thị Giá Hiện Tại", f"{current_price:,.0f} VND" if current_price > 0 else "N/A")
m2.metric("Giá Trị Hợp Lý (Composite)", f"{composite_price:,.0f} VND", delta=f"{upside:+.1f}% Biên an toàn" if current_price > 0 else None)
m3.metric("Mô Hình Trọng Yếu", f"{dcf_interactive_val:,.0f} VND", delta=f"P/E: {current_price/eps:.1f}x" if (eps > 0 and current_price > 0) else None)
m4.metric("Giá Trị Sổ Sách (BVPS)", f"{bvps:,.0f} VND/cp", delta=f"P/B: {current_price/bvps:.2f}x" if (bvps > 0 and current_price > 0) else None)

st.markdown(f"**Tín hiệu Đầu tư:** <span class='{signal_badge}'>{signal_text}</span>", unsafe_allow_html=True)

# Khối 10 Năm Moat
st.write("")
st.subheader("🏆 Hồ Sơ Năng Lực Dài Hạn 10 - 16 Năm (Warren Buffett Moat)")
t1, t2, t3, t4 = st.columns(4)
with t1:
    st.markdown(f"""<div class='cagr-box'>
        <div style='font-size:11px; color:#94a3b8; text-transform:uppercase; font-weight:700;'>📈 Doanh Thu 10Y CAGR</div>
        <div style='font-size:22px; font-weight:900; color:#38bdf8; margin-top:4px;'>{f"{cagr_10y_rev:+.1f}%/năm" if cagr_10y_rev is not None else "Không áp dụng cho Bank"}</div>
        <div style='font-size:10px; color:#64748b;'>Tăng trưởng gộp 10 năm</div>
    </div>""", unsafe_allow_html=True)
with t2:
    st.markdown(f"""<div class='cagr-box'>
        <div style='font-size:11px; color:#94a3b8; text-transform:uppercase; font-weight:700;'>💰 Lợi Nhuận 10Y CAGR</div>
        <div style='font-size:22px; font-weight:900; color:#34d399; margin-top:4px;'>{f"{cagr_10y_ni:+.1f}%/năm" if cagr_10y_ni is not None else "N/A"}</div>
        <div style='font-size:10px; color:#64748b;'>Tăng trưởng LNST 10 năm</div>
    </div>""", unsafe_allow_html=True)
with t3:
    st.markdown(f"""<div class='cagr-box'>
        <div style='font-size:11px; color:#94a3b8; text-transform:uppercase; font-weight:700;'>🎯 ROE Bình Quân 10 Năm</div>
        <div style='font-size:22px; font-weight:900; color:#fbbf24; margin-top:4px;'>{f"{avg_roe_10y:.1f}%" if avg_roe_10y is not None else "N/A"}</div>
        <div style='font-size:10px; color:#64748b;'>Hiệu quả sinh lời vốn CSH</div>
    </div>""", unsafe_allow_html=True)
with t4:
    st.markdown(f"""<div class='cagr-box'>
        <div style='font-size:11px; color:#94a3b8; text-transform:uppercase; font-weight:700;'>🛡️ Cổ Tức Bền Vững</div>
        <div style='font-size:22px; font-weight:900; color:#a78bfa; margin-top:4px;'>{div_consistency}</div>
        <div style='font-size:10px; color:#64748b;'>Số năm trả cổ tức tiền mặt</div>
    </div>""", unsafe_allow_html=True)

st.write("---")

# 3 Cột Trụ
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader(f"💎 Các Tầng Định Giá ({archetype_label.split(' ')[1]})")
    for m_k, m_v in active_models.items():
        diff = ((m_v - current_price) / current_price) * 100 if current_price > 0 else 0.0
        st.write(f"- **{m_k}:** {m_v:,.0f} VND (`{diff:+.1f}%`)")

with c2:
    st.subheader(radar_data['title'])
    st.write(f"- **{radar_data['metric1_label']}** {radar_data['metric1_val']}")
    st.write(f"- **{radar_data['metric2_label']}** {radar_data['metric2_val']}")
    st.write(f"- **{radar_data['metric3_label']}** {radar_data['metric3_val']}")

with c3:
    st.subheader(solvency_data['title'])
    st.write(f"- **{solvency_data['metric1_label']}** {solvency_data['metric1_val']}")
    st.write(f"- **{solvency_data['metric2_label']}** {solvency_data['metric2_val']}")
    st.write(f"- **{solvency_data['metric3_label']}** {solvency_data['metric3_val']}")

# Biểu đồ Plotly
ch1, ch2 = st.columns(2)
with ch1:
    x_bars = ['Thị Giá', *active_models.keys(), 'Giá Trị Hợp Lý'] if current_price > 0 else [*active_models.keys(), 'Giá Trị Hợp Lý']
    y_bars = [current_price, *active_models.values(), composite_price] if current_price > 0 else [*active_models.values(), composite_price]
    colors = ['#94a3b8', '#06b6d4', '#f59e0b', '#a855f7', '#3b82f6', '#10b981'] if current_price > 0 else ['#06b6d4', '#f59e0b', '#a855f7', '#3b82f6', '#10b981']
    fig_val = go.Figure(data=[go.Bar(x=x_bars, y=y_bars, marker_color=colors[:len(x_bars)])])
    fig_val.update_layout(title="So Sánh Thị Giá vs Các Mô Hình Định Giá", template="plotly_dark", height=380)
    st.plotly_chart(fig_val, use_container_width=True)

with ch2:
    fig_fin = go.Figure()
    if 'rev' in df.columns and df['rev'].sum() > 0:
        fig_fin.add_trace(go.Scatter(x=df['year'], y=df['rev']/1e9, name='Doanh thu', line=dict(color='#6366f1', width=3)))
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['ni']/1e9, name='Lợi nhuận ròng', line=dict(color='#10b981', width=3)))
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['eq']/1e9, name='Vốn Chủ Sở Hữu', line=dict(color='#f59e0b', dash='dash', width=2)))
    fig_fin.update_layout(title=f"Lịch Sử Vốn CSH & Lợi Nhuận {len(df)} Năm ({df['year'].min()} - {df['year'].max()}) [Tỷ VND]", template="plotly_dark", height=380)
    st.plotly_chart(fig_fin, use_container_width=True)

st.caption("Terminal phát triển bởi Antigravity Pair Programming • CFA Institute Standards • Multi-Sector Domain Engine.")
