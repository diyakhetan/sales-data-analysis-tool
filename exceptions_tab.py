import streamlit as st
import pandas as pd
import tempfile
import os

def show_exceptions_tab(mapped_df):
    st.header("Sales Data Exception Reports")

    st.write("Select exception types to generate reports:")
    options = {
        "Negative Sales or Quantity": "negatives",
        "Duplicate Rows": "duplicates",
        "Missing Critical Fields": "missing_fields",
        "Outliers in Sales Amt or Qty": "outliers",
        "Invalid Invoice Dates": "invalid_dates",
        "Zero Qty with non-zero Sales or vice versa": "mismatch_sales_qty"
    }

    selected = [opt for opt in options if st.checkbox(opt)]

    reports = {}

    if "Negative Sales or Quantity" in selected:
        negatives = mapped_df[(mapped_df["Sales Amt"] < 0) | (mapped_df["Qty"] < 0)]
        reports["Negative Sales or Qty"] = negatives

    if "Duplicate Rows" in selected:
        duplicates = mapped_df[mapped_df.duplicated()]
        reports["Duplicate Rows"] = duplicates

    if "Missing Critical Fields" in selected:
        critical_cols = ["State", "Dealer", "Inv Date"]
        missing = mapped_df[mapped_df[critical_cols].isnull().any(axis=1)]
        reports["Missing Critical Fields"] = missing

    if "Outliers in Sales Amt or Qty" in selected:
        for col in ["Sales Amt", "Qty"]:
            q1 = mapped_df[col].quantile(0.25)
            q3 = mapped_df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = mapped_df[(mapped_df[col] < (q1 - 1.5 * iqr)) | (mapped_df[col] > (q3 + 1.5 * iqr))]
            reports[f"Outliers in {col}"] = outliers

    if "Invalid Invoice Dates" in selected and "Inv Date" in mapped_df.columns:
        mapped_df['Inv Date'] = pd.to_datetime(mapped_df['Inv Date'], errors='coerce')
        invalid_dates = mapped_df[mapped_df['Inv Date'] > pd.Timestamp.today()]
        reports["Future/Invalid Dates"] = invalid_dates

    if "Zero Qty with non-zero Sales or vice versa" in selected:
        mismatch = mapped_df[((mapped_df['Qty'] == 0) & (mapped_df['Sales Amt'] != 0)) | 
                             ((mapped_df['Sales Amt'] == 0) & (mapped_df['Qty'] != 0))]
        reports["Zero Qty / Non-zero Sales Mismatch"] = mismatch

    for title, data in reports.items():
        st.subheader(title)
        st.dataframe(data)

    if reports:
        if st.button("Export Reports to Excel"):
            # Create a temp file manually (without 'with' block to avoid locking on Windows)
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            output_path = tmp_file.name
            tmp_file.close()  # Explicitly close so it’s not locked on Windows

            try:
                # Write Excel file
                with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                    for title, df in reports.items():
                        df.to_excel(writer, sheet_name=title[:31], index=False)

                # Read and allow download
                with open(output_path, "rb") as f:
                    st.download_button(
                        "Download Excel File",
                        f.read(),
                        file_name="exception_reports.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            finally:
                # Clean up the file afterwards
                os.remove(output_path)
    else:
        st.info("No exception types selected.")
