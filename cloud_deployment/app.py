"""
========================================================================================
FINANCIAL RADAR & REAL-TIME VALUATION TERMINAL (CLOUD & MOBILE EDITION)
Framework: Streamlit + CFA Equity Valuation + Howard Schilit Audit Radar
Triển khai: Streamlit Community Cloud / HuggingFace Spaces (Miễn phí 100%)
========================================================================================
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. Cấu hình trang tối ưu cho điện thoại & Desktop
st.set_page_config(
    page_title="Financial Radar & Valuation Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS cho phong cách Modern Dark Mode
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f8fafc; }
    .stMetric { background: rgba(30, 41, 59, 0.6); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); }
    .badge-buy { background-color: #064e3b; color: #34d399; padding: 4px 10px; border-radius: 9999px; font-weight: bold; }
    .badge-hold { background-color: #78350f; color: #fbbf24; padding: 4px 10px; border-radius: 9999px; font-weight: bold; }
    .badge-sell { background-color: #881337; color: #f87171; padding: 4px 10px; border-radius: 9999px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Financial Radar & Real-Time Valuation Terminal")
st.caption("CFA Institute Valuation • Howard Schilit Financial Shenanigans • Altman Z''-Score")

# 2. Thanh tìm kiếm Ticker & Gợi ý nhanh
col_search, col_btn = st.columns([4, 1])
with col_search:
    ticker_input = st.text_input("Nhập mã chứng khoán (HOSE, HNX, UPCoM):", value="FPT").upper().strip()

# Các nút bấm nhanh
preset_cols = st.columns(6)
presets = ["FPT", "GAS", "HPG", "VNM", "MWG", "VCB"]
for idx, p in enumerate(presets):
    if preset_cols[idx].button(p, use_container_width=True):
        ticker_input = p

if not ticker_input:
    st.warning("Vui lòng nhập một mã chứng khoán để phân tích.")
    st.stop()

# 3. Kéo dữ liệu thời gian thực
@st.cache_data(ttl=300) # Cache 5 phút để tránh gọi API lặp lại
def fetch_stock_data(ticker):
    yf_ticker = f"{ticker}.VN" if not ticker.endswith(".VN") else ticker
    stock = yf.Ticker(yf_ticker)
    info = stock.info
    bs = stock.balance_sheet
    inc = stock.financials
    cf = stock.cashflow
    return info, bs, inc, cf

with st.spinner(f"Đang phân tích dữ liệu BCTC và định giá thời gian thực cho mã {ticker_input}..."):
    try:
        info, bs, inc, cf = fetch_stock_data(ticker_input)
        if inc.empty or bs.empty:
            st.error(f"Không tìm thấy dữ liệu tài chính cho mã '{ticker_input}'. Vui lòng thử lại mã khác.")
            st.stop()
    except Exception as e:
        st.error(f"Lỗi khi kéo dữ liệu: {e}")
        st.stop()

dates = sorted(inc.columns)

def safe_get(df, row, col, default=0.0):
    if not df.empty and row in df.index and col in df.columns:
        val = df.loc[row, col]
        return float(val) if pd.notnull(val) else default
    return default

# Dữ liệu thị trường
current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
shares = info.get('sharesOutstanding') or info.get('impliedSharesOutstanding') or 0
if shares == 0 and 'Ordinary Shares Number' in bs.index:
    shares = safe_get(bs, 'Ordinary Shares Number', dates[-1])

beta = info.get('beta') or 1.0
if beta < 0.4 or beta > 2.5: beta = 1.0

company_name = info.get('shortName') or info.get('longName') or ticker_input
sector = info.get('sector', 'Tổng hợp')
industry = info.get('industry', 'Tổng hợp')

# Chuỗi thời gian 4 năm
records = []
for d in dates:
    yr = d.strftime('%Y')
    rev = safe_get(inc, 'Total Revenue', d)
    gp = safe_get(inc, 'Gross Profit', d)
    op = safe_get(inc, 'Operating Income', d)
    ebit = safe_get(inc, 'EBIT', d) or op
    ebitda = safe_get(inc, 'EBITDA', d)
    ni = safe_get(inc, 'Net Income', d)
    depr = safe_get(inc, 'Reconciled Depreciation', d) or safe_get(cf, 'Depreciation And Amortization', d)
    
    ta = safe_get(bs, 'Total Assets', d)
    ca = safe_get(bs, 'Current Assets', d)
    cl = safe_get(bs, 'Current Liabilities', d)
    tl = safe_get(bs, 'Total Liabilities Net Minority Interest', d) or (ta - safe_get(bs, 'Stockholders Equity', d))
    eq = safe_get(bs, 'Stockholders Equity', d)
    re = safe_get(bs, 'Retained Earnings', d)
    ar = safe_get(bs, 'Accounts Receivable', d)
    inv = safe_get(bs, 'Inventory', d)
    net_ppe = safe_get(bs, 'Net PPE', d)
    debt = safe_get(bs, 'Total Debt', d)
    cash = safe_get(bs, 'Cash Cash Equivalents And Short Term Investments', d)
    
    cfo = safe_get(cf, 'Operating Cash Flow', d)
    capex = abs(safe_get(cf, 'Capital Expenditure', d))
    fcf = safe_get(cf, 'Free Cash Flow', d) or (cfo - capex)
    div_paid = abs(safe_get(cf, 'Cash Dividends Paid', d))
    
    records.append({
        'year': yr, 'rev': rev, 'gp': gp, 'ebit': ebit, 'ebitda': ebitda, 'ni': ni,
        'depr': depr, 'ta': ta, 'ca': ca, 'cl': cl, 'tl': tl, 'eq': eq, 're': re,
        'ar': ar, 'inv': inv, 'net_ppe': net_ppe, 'debt': debt, 'cash': cash,
        'cfo': cfo, 'capex': capex, 'fcf': fcf, 'div_paid': div_paid
    })

df = pd.DataFrame(records)
latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) >= 2 else latest

# Tính toán Shenanigans & Solvency
dsri = (latest['ar'] / latest['rev']) / (prev['ar'] / prev['rev']) if (latest['rev'] > 0 and prev['ar'] > 0) else 1.0
gm_curr = latest['gp'] / latest['rev'] if latest['rev'] > 0 else 0.2
gm_prev = prev['gp'] / prev['rev'] if prev['rev'] > 0 else 0.2
gmi = gm_prev / gm_curr if gm_curr > 0 else 1.0
sgi = latest['rev'] / prev['rev'] if prev['rev'] > 0 else 1.0
tata = (latest['ni'] - latest['cfo']) / latest['ta'] if latest['ta'] > 0 else 0.0

m_score = -4.84 + 0.920*dsri + 0.528*gmi + 0.404*1.0 + 0.892*sgi + 0.115*1.0 - 0.172*1.0 + 4.037*tata + 0.0327*1.0

# Altman Z''
x1 = (latest['ca'] - latest['cl']) / latest['ta'] if latest['ta'] > 0 else 0.2
x2 = latest['re'] / latest['ta'] if latest['ta'] > 0 else 0.1
x3 = latest['ebit'] / latest['ta'] if latest['ta'] > 0 else 0.1
x4 = latest['eq'] / latest['tl'] if latest['tl'] > 0 else 2.0
z_score = 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4

net_debt = latest['debt'] - latest['cash']
net_cash_per_share = -net_debt / shares if (shares > 0 and net_debt < 0) else 0.0

# 4. Sidebar: Bộ mô phỏng tương tác WACC & Growth
st.sidebar.header("🎮 Tham Số Định Giá (DCF Simulator)")
wacc_input = st.sidebar.slider("Chi Phí Vốn (WACC %):", min_value=7.5, max_value=13.5, value=10.0, step=0.25) / 100
growth_input = st.sidebar.slider("Tăng Trưởng Dài Hạn (g %):", min_value=1.0, max_value=4.0, value=2.5, step=0.25) / 100

# Tính toán các mô hình định giá
base_fcf = latest['fcf'] if latest['fcf'] > 0 else df['fcf'].mean()
if base_fcf <= 0: base_fcf = latest['ni'] * 0.7

curr_fcf = base_fcf
pv_fcfs = []
for yr in range(1, 6):
    curr_fcf *= 1.06
    pv_fcfs.append(curr_fcf / ((1 + wacc_input) ** yr))
terminal_val = (curr_fcf * (1 + growth_input)) / (wacc_input - growth_input)
pv_term = terminal_val / ((1 + wacc_input) ** 5)
dcf_equity = sum(pv_fcfs) + pv_term - net_debt
dcf_price = max(0.0, dcf_equity / shares) if shares > 0 else 0.0

# Owner Earnings
maint_capex = latest['capex'] * 0.60
oe = latest['ni'] + latest['depr'] - maint_capex
if oe <= 0: oe = df['ni'].mean()
oe_price = max(0.0, ((oe * 1.03) / (0.10 - 0.03)) / shares) if shares > 0 else 0.0

# Graham
eps = latest['ni'] / shares if shares > 0 else 0.0
bvps = latest['eq'] / shares if shares > 0 else 0.0
graham_num = np.sqrt(22.5 * eps * bvps) if (eps > 0 and bvps > 0) else 0.0
graham_int = eps * (8.5 + 2 * 5.0) * (4.4 / 3.5) if eps > 0 else 0.0
graham_price = (graham_num * 0.5 + graham_int * 0.5) if graham_num > 0 else graham_int

# DDM
avg_div = df['div_paid'].values[-3:].mean() if len(df) >= 3 else latest['div_paid']
dps = avg_div / shares if shares > 0 else 0.0
ddm_price = max(0.0, (dps * 1.03) / (0.09 - 0.03)) if dps > 0 else 0.0

# Multiples
pe_price = eps * 14.0 if eps > 0 else 0.0

active_models = {'DCF (FCFF)': dcf_price, 'Owner Earnings': oe_price, 'Graham Value': graham_price, 'Relative P/E': pe_price}
weights = {'DCF (FCFF)': 0.35, 'Owner Earnings': 0.25, 'Relative P/E': 0.25, 'Graham Value': 0.15}
if ddm_price > 0:
    active_models['Dividend DDM'] = ddm_price
    weights = {'DCF (FCFF)': 0.30, 'Owner Earnings': 0.20, 'Relative P/E': 0.25, 'Dividend DDM': 0.15, 'Graham Value': 0.10}

tot_w = sum([weights[k] for k in active_models if active_models[k] > 0])
composite_price = sum([active_models[k] * weights[k] for k in active_models if active_models[k] > 0]) / tot_w if tot_w > 0 else 0.0
upside = ((composite_price - current_price) / current_price) * 100 if current_price > 0 else 0.0

if upside >= 25.0: signal_badge, signal_text = "badge-buy", "🟢 STRONG BUY"
elif upside >= 10.0: signal_badge, signal_text = "badge-buy", "🟢 BUY"
elif upside >= -10.0: signal_badge, signal_text = "badge-hold", "🟡 FAIRLY VALUED"
else: signal_badge, signal_text = "badge-sell", "🔴 OVERVALUED"

# 5. Hiển thị Header & Metrics
st.markdown(f"### **{ticker_input}** — {company_name}")
st.write(f"**Ngành:** {sector} • {industry} | **Vốn hóa:** {current_price*shares/1e9:,.0f} Tỷ VND")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Thị Giá Hiện Tại", f"{current_price:,.0f} VND")
m2.metric("Giá Trị Hợp Lý (Composite)", f"{composite_price:,.0f} VND", delta=f"{upside:+.1f}% Biên an toàn")
m3.metric("DCF Tương Tác", f"{dcf_price:,.0f} VND", delta=f"WACC: {wacc_input*100:.1f}%")
m4.metric("Két Tiền Mặt Ròng", f"{net_cash_per_share:,.0f} VND/cp" if net_cash_per_share > 0 else "Nợ ròng")

st.markdown(f"**Tín hiệu Đầu tư:** <span class='{signal_badge}'>{signal_text}</span>", unsafe_allow_html=True)
st.write("---")

# 6. Ba Cột Trụ Phân Tích
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("💎 5 Tầng Định Giá")
    for m_k, m_v in active_models.items():
        diff = ((m_v - current_price) / current_price) * 100 if current_price > 0 else 0.0
        st.write(f"- **{m_k}:** {m_v:,.0f} VND (`{diff:+.1f}%`)")
        
with c2:
    st.subheader("🚦 Radar Gian Lận (Schilit)")
    st.write(f"- **Beneish M-Score:** `{m_score:.3f}` ({'SẠCH' if m_score < -2.22 else ('VÙNG XÁM' if m_score < -1.78 else 'RỦI RO')})")
    cfo_ni = latest['cfo'] / latest['ni'] if latest['ni'] > 0 else 0
    st.write(f"- **Chất lượng Dồn tích (CFO/NI):** `{cfo_ni:.2f}x` ({'Lãi thật' if cfo_ni >= 1.0 else 'Dồn tích cao'})")
    st.write(f"- **Vòng quay Phải thu (DSO):** `{(latest['ar']/latest['rev'])*365:.0f} ngày`")

with c3:
    st.subheader("🏰 Sức Khỏe & Vỡ Nợ")
    st.write(f"- **Altman Z''-Score:** `{z_score:.2f}` ({'SIÊU AN TOÀN' if z_score > 2.6 else 'VÙNG XÁM'})")
    st.write(f"- **Tiền mặt & Đầu tư ngắn hạn:** `{latest['cash']/1e9:,.0f} Tỷ VND`")
    st.write(f"- **Hệ số thanh toán hiện hành:** `{latest['ca']/latest['cl']:.2f}x`")

# 7. Biểu đồ tương tác Plotly
ch1, ch2 = st.columns(2)
with ch1:
    fig_val = go.Figure(data=[
        go.Bar(
            x=['Thị Giá', *active_models.keys(), 'Giá Trị Hợp Lý'],
            y=[current_price, *active_models.values(), composite_price],
            marker_color=['#94a3b8', '#06b6d4', '#f59e0b', '#a855f7', '#3b82f6', '#10b981']
        )
    ])
    fig_val.update_layout(title="So Sánh Thị Giá vs Các Mô Hình Định Giá", template="plotly_dark", height=350)
    st.plotly_chart(fig_val, use_container_width=True)

with ch2:
    fig_fin = go.Figure()
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['rev']/1e9, name='Doanh thu', line=dict(color='#6366f1', width=3)))
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['ni']/1e9, name='Lợi nhuận ròng', line=dict(color='#10b981', width=3)))
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['cfo']/1e9, name='Dòng tiền CFO', line=dict(color='#f59e0b', dash='dash', width=2)))
    fig_fin.update_layout(title="Quỹ Đạo Tài Chính 4 Năm (Tỷ VND)", template="plotly_dark", height=350)
    st.plotly_chart(fig_fin, use_container_width=True)

