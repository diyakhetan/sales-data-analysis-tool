import streamlit as st
import pandas as pd
from io import BytesIO

import matplotlib.pyplot as plt
import io
from fpdf import FPDF
from PIL import Image
import tempfile
import streamlit as st
import plotly.express as px
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.graph_objects as go






def generate_excel(reports_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in reports_dict.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()

def show_reports_tab(merged_df):
    st.header("📊 Reports Generator")

    if merged_df is None or merged_df.empty:
        st.warning("⚠️ Please complete the ETL pipeline to access reports.")
        return

    st.subheader("Select Reports to Generate")

    report_options = [
        "Top Customers Report",
        "Product Performance Report",
        "Sales by Region/Channel",
        "Sales Summary Report"
    ]

    selected_reports = st.multiselect("Choose reports to generate:", report_options)

    reports = {}
    st.session_state["reports"] = reports


    if "Top Customers Report" in selected_reports:
        if "Dealer_Name" in merged_df.columns and "Sales Amt" in merged_df.columns:
            top_customers = (
                merged_df.groupby("Dealer_Name")[["Sales Amt", "Qty"]]
                .sum()
                .sort_values(by="Sales Amt", ascending=False)
                .reset_index()
            )
            reports["Top Customers"] = top_customers
            st.write("### Top Customers Report", top_customers)

    if "Product Performance Report" in selected_reports:
        if "Mat Desc" in merged_df.columns and "Sales Amt" in merged_df.columns:
            product_perf = (
                merged_df.groupby("Mat Desc")[["Sales Amt", "Qty"]]
                .sum()
                .sort_values(by="Sales Amt", ascending=False)
                .reset_index()
            )
            reports["Product Performance"] = product_perf
            st.subheader("Product Performance Report")
            st.dataframe(product_perf.head(10))

            fig = px.bar(
                product_perf.head(10),
                x="Mat Desc",
                y="Sales Amt",
                text_auto='.2s',
                title="Top 10 Products by Sales",
                labels={"Mat Desc": "Product", "Sales Amt": "Sales Amount (₹)"}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)


    if "Sales by Region/Channel" in selected_reports:
        if "State" in merged_df.columns and "Sales Amt" in merged_df.columns:
            sales_by_region = (
                merged_df.groupby("State")[["Sales Amt", "Qty"]]
                .sum()
                .sort_values(by="Sales Amt", ascending=False)
                .reset_index()
            )
            reports["Sales by Region"] = sales_by_region
            st.write("### Sales by Region/Channel", sales_by_region)

    if "Sales Summary Report" in selected_reports:
        if "Month" in merged_df.columns and "Year" in merged_df.columns:
            summary = (
                merged_df.groupby(["Year", "Month"])[["Sales Amt", "Qty"]]
                .sum()
                .sort_values(by=["Year", "Month"])
                .reset_index()
            )
            reports["Sales Summary"] = summary
            st.subheader("Sales Summary Report")
            st.dataframe(summary)

            summary["Period"] = summary["Year"].astype(str) + "-" + summary["Month"].astype(str)
            fig = px.line(
                summary,
                x="Period",
                y="Sales Amt",
                title="Monthly Sales Trend",
                labels={"Sales Amt": "Sales Amount (₹)", "Period": "Month-Year"},
                markers=True
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)


    if reports:
        excel_data = generate_excel(reports)
        st.download_button(
            label="📥 Download All Reports (Excel)",
            data=excel_data,
            file_name="sales_reports.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        pdf_data = generate_report_pdf(reports)
        st.download_button(
            label="📄 Download Report Summary (PDF)",
            data=pdf_data,
            file_name="sales_report_summary.pdf",
            mime="application/pdf"
        )

    else:
        st.info("Select at least one report to generate.")
        


import os

from matplotlib.ticker import FuncFormatter

def generate_report_pdf(reports):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    def format_in_lakhs(x, _):
        return f'₹{x*1e-5:.1f}L'

    for report_name, df in reports.items():
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, report_name, ln=True)

        fig, ax = plt.subplots(figsize=(6.5, 3.5))
        ax.yaxis.set_major_formatter(FuncFormatter(format_in_lakhs))

        if report_name == "Top Customers":
            chart_data = df.head(10)
            chart_data.plot(kind='bar', x='Dealer_Name', y='Sales Amt', ax=ax, color='#1f77b4')
            ax.set_title("Top 10 Customers by Sales")
            ax.set_xlabel("Customer")
            ax.set_ylabel("Sales Amount (₹ Lakhs)")
            plt.xticks(rotation=45, ha='right')

        elif report_name == "Product Performance":
            chart_data = df.head(10)
            chart_data.plot(kind='bar', x='Mat Desc', y='Sales Amt', ax=ax, color='#2ca02c')
            ax.set_title("Top 10 Products by Sales")
            ax.set_xlabel("Product")
            ax.set_ylabel("Sales Amount (₹ Lakhs)")
            plt.xticks(rotation=45, ha='right')

        elif report_name == "Sales by Region":
            chart_data = df.head(15)
            chart_data.plot(kind='bar', x='State', y='Sales Amt', ax=ax, color='#d62728')
            ax.set_title("Sales by State")
            ax.set_xlabel("State")
            ax.set_ylabel("Sales Amount (₹ Lakhs)")
            plt.xticks(rotation=45, ha='right')

        elif report_name == "Sales Summary":
            df["Period"] = df["Year"].astype(str) + "-" + df["Month"].astype(str)
            df["Period"] = pd.to_datetime(df["Period"] + "-01")
            df_sorted = df.sort_values("Period")
            df_sorted.plot(kind='line', x='Period', y='Sales Amt', ax=ax, color='#ff7f0e', marker='o')
            ax.set_title("Monthly Sales Trend")
            ax.set_xlabel("Period")
            ax.set_ylabel("Sales Amount (₹ Lakhs)")
            ax.grid(True)

        fig.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img = Image.open(buf)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
            img.save(tmp_img.name)
            pdf.image(tmp_img.name, w=180)
            os.unlink(tmp_img.name)

        plt.close(fig)

        pdf.set_font("Arial", "", 10)
        for i in range(min(len(df), 10)):
            row = df.iloc[i].astype(str).tolist()
            pdf.cell(0, 10, " | ".join(row), ln=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf.output(tmp_pdf.name)
        tmp_pdf_path = tmp_pdf.name

    with open(tmp_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    os.unlink(tmp_pdf_path)

    return BytesIO(pdf_bytes)

def show_forecast_tab(df):
    st.header("📈 Forecast Sales Using Prophet")

    if df is None or df.empty:
        st.warning("⚠️ Please load data through ETL first.")
        return

    st.subheader("Configure Forecast")

    st.write("Columns in dataframe:", df.columns.tolist())


    df['Inv Date'] = pd.to_datetime(df['Inv Date'])
    df['Month'] = df['Inv Date'].dt.to_period('M').dt.to_timestamp()

    df['Month'] = df['Inv Date'].dt.to_period('M').dt.to_timestamp()

    sales_monthly = df.groupby('Month')['Sales Amt'].sum().reset_index()
    sales_monthly.columns = ['ds', 'y']

    forecast_period = st.slider("Months to Forecast", min_value=1, max_value=24, value=6)

    model = Prophet()
    with st.spinner("Training the model..."):
        model.fit(sales_monthly)

    future = model.make_future_dataframe(periods=forecast_period, freq='ME')
    forecast = model.predict(future)

    st.success("Forecast generated!")

    actual = forecast[forecast['ds'] <= sales_monthly['ds'].max()]
    predicted = forecast[forecast['ds'] > sales_monthly['ds'].max()]

    # Create figure
    fig = go.Figure()

    # Actual data in blue
    fig.add_trace(go.Scatter(
        x=actual['ds'],
        y=actual['yhat'],
        mode='lines+markers',
        name='Actual (Fitted)',
        line=dict(color='blue')
    ))

    # Forecast data in orange
    fig.add_trace(go.Scatter(
        x=predicted['ds'],
        y=predicted['yhat'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='orange', dash='dash')
    ))

    # Add confidence interval
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        mode='lines',
        name='Upper Bound',
        line=dict(width=0),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        mode='lines',
        name='Lower Bound',
        fill='tonexty',
        line=dict(width=0),
        fillcolor='rgba(255,165,0,0.2)',
        showlegend=True
    ))

    # Layout
    fig.update_layout(
        title='Sales Forecast',
        xaxis_title='Month',
        yaxis_title='Sales Amount',
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    forecast_table = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(forecast_period)
    forecast_table.columns = ['Month', 'Predicted Sales', 'Lower Bound', 'Upper Bound']
    st.write("### Forecast Table")
    st.dataframe(forecast_table)
