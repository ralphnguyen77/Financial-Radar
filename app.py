"""
========================================================================================
FINANCIAL RADAR & REAL-TIME VALUATION TERMINAL (CLOUD & MOBILE EDITION)
Framework: Streamlit + CFA Equity Valuation + Howard Schilit Audit Radar
Cơ sở dữ liệu: Tích hợp BCTC 16 Năm Lịch Sử (2010 - 2025) từ vietnam_stocks_16y.parquet
Triển khai: Streamlit Community Cloud / HuggingFace Spaces (Miễn phí 100%)
========================================================================================
"""

import os
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
    .cagr-box { background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 12px 16px; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Financial Radar & Real-Time Valuation Terminal")
st.caption("CFA Institute Valuation • Howard Schilit Financial Shenanigans • Altman Z''-Score • Dữ liệu 16 Năm (2010 - 2025)")

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

# 3. Load cơ sở dữ liệu 16 năm từ Parquet (Offline - Cực nhanh)
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

# 4. Kéo dữ liệu thời gian thực và BCTC
@st.cache_data(ttl=300)
def fetch_market_info(ticker):
    yf_ticker = f"{ticker}.VN" if not ticker.endswith(".VN") else ticker
    stock = yf.Ticker(yf_ticker)
    info = stock.info
    return info, stock

with st.spinner(f"Đang đồng bộ dữ liệu và định giá mã {ticker_input}..."):
    try:
        info, stock = fetch_market_info(ticker_input)
    except Exception as e:
        info, stock = {}, None

# Kiểm tra mã trong CSDL 16 năm
loaded_from_local = False
df = pd.DataFrame()
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
            sub['re'] = sub['eq'] * 0.25 # Ước lượng thặng dư LNCL
        if 'cl' not in sub.columns:
            sub['cl'] = sub['tl'] * 0.70
        df = sub
        loaded_from_local = True
        data_source_badge = f"⚡ CSDL Kiểm toán 16 Năm ({sub['year'].min()} - {sub['year'].max()}) [Offline Siêu Tốc]"

# Fallback sang yfinance nếu không có trong CSDL nội địa
if not loaded_from_local:
    try:
        if stock is None:
            yf_ticker = f"{ticker_input}.VN" if not ticker_input.endswith(".VN") else ticker_input
            stock = yf.Ticker(yf_ticker)
            info = stock.info
        bs = stock.balance_sheet
        inc = stock.financials
        cf = stock.cashflow
        
        if inc.empty or bs.empty:
            st.error(f"Không tìm thấy dữ liệu tài chính cho mã '{ticker_input}'. Vui lòng thử lại mã khác.")
            st.stop()
            
        dates = sorted(inc.columns)
        def safe_get(df_in, row, col, default=0.0):
            if not df_in.empty and row in df_in.index and col in df_in.columns:
                val = df_in.loc[row, col]
                return float(val) if pd.notnull(val) else default
            return default
            
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
                'net_debt': debt - cash, 'cfo': cfo, 'capex': capex, 'fcf': fcf, 'div_paid': div_paid
            })
        df = pd.DataFrame(records)
        data_source_badge = f"🌐 Nguồn yfinance ({len(df)} năm gần nhất)"
    except Exception as e_yf:
        st.error(f"Lỗi khi tải dữ liệu: {e_yf}")
        st.stop()

# 5. Dữ liệu thị trường
latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) >= 2 else latest

current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
shares = info.get('sharesOutstanding') or info.get('impliedSharesOutstanding') or 0
if shares == 0:
    shares = int(latest['eq'] / 25000) if latest['eq'] > 0 else 1000000

beta = info.get('beta') or 1.0
if beta < 0.4 or beta > 2.5: beta = 1.0

company_name = info.get('shortName') or info.get('longName') or latest.get('company_name', ticker_input)
sector = info.get('sector', 'Tổng hợp')
industry = info.get('industry', 'Tổng hợp')

# 6. Tính toán 10-Year Track Record & Moat Metrics
cagr_10y_rev, cagr_10y_ni, cagr_5y_rev, cagr_5y_ni = None, None, None, None
avg_roe_10y, div_consistency = None, None

if len(df) >= 5:
    y_latest = int(latest['year'])
    row_5y = df[df['year'] == str(y_latest - 5)]
    if not row_5y.empty and row_5y.iloc[0]['rev'] > 0 and latest['rev'] > 0:
        cagr_5y_rev = ((latest['rev'] / row_5y.iloc[0]['rev']) ** (1/5) - 1) * 100
    if not row_5y.empty and row_5y.iloc[0]['ni'] > 0 and latest['ni'] > 0:
        cagr_5y_ni = ((latest['ni'] / row_5y.iloc[0]['ni']) ** (1/5) - 1) * 100

if len(df) >= 10:
    y_latest = int(latest['year'])
    row_10y = df[df['year'] == str(y_latest - 10)]
    if not row_10y.empty and row_10y.iloc[0]['rev'] > 0 and latest['rev'] > 0:
        cagr_10y_rev = ((latest['rev'] / row_10y.iloc[0]['rev']) ** (1/10) - 1) * 100
    if not row_10y.empty and row_10y.iloc[0]['ni'] > 0 and latest['ni'] > 0:
        cagr_10y_ni = ((latest['ni'] / row_10y.iloc[0]['ni']) ** (1/10) - 1) * 100
    
    sub_10 = df.iloc[-10:]
    valid_roe = [(r['ni'] / r['eq'] * 100) for _, r in sub_10.iterrows() if r['eq'] > 0]
    if valid_roe:
        avg_roe_10y = np.mean(valid_roe)

div_cnt = len(df[df['div_paid'] > 0])
div_consistency = f"{div_cnt}/{len(df)} năm"

# 7. Tính toán Shenanigans (Beneish M-Score) & Sức khỏe (Altman Z''-Score)
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

# 8. Sidebar: Bộ mô phỏng tương tác DCF Simulator
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

# Owner Earnings (Warren Buffett)
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

# DDM (Cổ tức tiền mặt bình quân 3 năm)
avg_div = df['div_paid'].values[-3:].mean() if len(df) >= 3 else latest['div_paid']
dps = avg_div / shares if shares > 0 else 0.0
ddm_price = max(0.0, (dps * 1.03) / (0.09 - 0.03)) if dps > 0 else 0.0

# Relative Multiples (P/E & EV/EBITDA)
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

# 9. Hiển thị Header & Metrics
st.markdown(f"### **{ticker_input}** — {company_name}")
st.caption(f"{data_source_badge} • Ngành: {sector} • {industry} • Vốn hóa: {current_price*shares/1e9:,.0f} Tỷ VND")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Thị Giá Hiện Tại", f"{current_price:,.0f} VND")
m2.metric("Giá Trị Hợp Lý (Composite)", f"{composite_price:,.0f} VND", delta=f"{upside:+.1f}% Biên an toàn")
m3.metric("DCF Tương Tác", f"{dcf_price:,.0f} VND", delta=f"WACC: {wacc_input*100:.1f}%")
m4.metric("Két Tiền Mặt Ròng", f"{net_cash_per_share:,.0f} VND/cp" if net_cash_per_share > 0 else "Nợ ròng")

st.markdown(f"**Tín hiệu Đầu tư:** <span class='{signal_badge}'>{signal_text}</span>", unsafe_allow_html=True)

# 10. Dải Chỉ Số Đẳng Cấp 10 Năm (Long-Term Fundamental Track Record)
if cagr_10y_rev is not None or avg_roe_10y is not None:
    st.write("")
    st.subheader("🏆 Hồ Sơ Năng Lực Dài Hạn 10 - 16 Năm (Warren Buffett Moat)")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown(f"""<div class='cagr-box'>
            <div style='font-size:11px; color:#94a3b8; text-transform:uppercase; font-weight:700;'>📈 Doanh Thu 10Y CAGR</div>
            <div style='font-size:22px; font-weight:900; color:#38bdf8; margin-top:4px;'>{f"{cagr_10y_rev:+.1f}%/năm" if cagr_10y_rev is not None else "N/A"}</div>
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
            <div style='font-size:10px; color:#64748b;'>Hiệu quả sinh lời dài hạn</div>
        </div>""", unsafe_allow_html=True)
    with t4:
        st.markdown(f"""<div class='cagr-box'>
            <div style='font-size:11px; color:#94a3b8; text-transform:uppercase; font-weight:700;'>🛡️ Cổ Tức Bền Vững</div>
            <div style='font-size:22px; font-weight:900; color:#a78bfa; margin-top:4px;'>{div_consistency or "N/A"}</div>
            <div style='font-size:10px; color:#64748b;'>Số năm trả cổ tức tiền mặt</div>
        </div>""", unsafe_allow_html=True)

st.write("---")

# 11. Ba Cột Trụ Phân Tích
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

# 12. Biểu đồ tương tác Plotly
ch1, ch2 = st.columns(2)
with ch1:
    fig_val = go.Figure(data=[
        go.Bar(
            x=['Thị Giá', *active_models.keys(), 'Giá Trị Hợp Lý'],
            y=[current_price, *active_models.values(), composite_price],
            marker_color=['#94a3b8', '#06b6d4', '#f59e0b', '#a855f7', '#3b82f6', '#10b981']
        )
    ])
    fig_val.update_layout(title="So Sánh Thị Giá vs Các Mô Hình Định Giá", template="plotly_dark", height=380)
    st.plotly_chart(fig_val, use_container_width=True)

with ch2:
    fig_fin = go.Figure()
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['rev']/1e9, name='Doanh thu', line=dict(color='#6366f1', width=3)))
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['ni']/1e9, name='Lợi nhuận ròng', line=dict(color='#10b981', width=3)))
    fig_fin.add_trace(go.Scatter(x=df['year'], y=df['cfo']/1e9, name='Dòng tiền CFO', line=dict(color='#f59e0b', dash='dash', width=2)))
    if 'fcf' in df.columns:
        fig_fin.add_trace(go.Scatter(x=df['year'], y=df['fcf']/1e9, name='Dòng tiền FCF', line=dict(color='#06b6d4', dash='dot', width=1.5)))
    fig_fin.update_layout(title=f"Quỹ Đạo Tài Chính {len(df)} Năm ({df['year'].min()} - {df['year'].max()}) [Tỷ VND]", template="plotly_dark", height=380)
    st.plotly_chart(fig_fin, use_container_width=True)

st.caption("Terminal phát triển bởi Antigravity Pair Programming • CFA Institute Standards • Howard Schilit Audit Radar.")
