import streamlit as st
import pdfplumber
import pandas as pd
import re
import tempfile

st.caption("Trial version for CA testing")
st.title("CA Bank Statement Cleaner")

uploaded_file = st.file_uploader("Upload Bank Statement PDF", type="pdf")

amount_filter = st.selectbox(
    "Remove withdrawals below (₹)",
    ["No Filter", "1000", "3000", "5000"]
)

if uploaded_file:

    lines = []

    # Extract text from PDF
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))

    transactions = []

    date_pattern = r"\d{2} \w{3} \d{2}"

    for line in lines:

        dates = re.findall(date_pattern, line)

        if len(dates) >= 1:

            numbers = re.findall(r"\d{1,3}(?:,\d{3})*\.\d{2}", line)

            desc = re.sub(date_pattern, "", line)

            transactions.append({
                "Date": dates[0],
                "Description": desc[:60],
                "Amount": numbers[0] if numbers else None
            })

    df = pd.DataFrame(transactions)

    # Clean numeric column
    df["Amount"] = df["Amount"].str.replace(",", "", regex=False)
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    df = df.dropna(subset=["Amount"])

    if amount_filter != "No Filter":
        limit = int(amount_filter)
        df = df[df["Amount"] >= limit]

    st.subheader("Clean Transactions")
    st.dataframe(df)

    # -------- SUMMARY --------
    st.subheader("Summary")

    total_withdrawals = df["Amount"].sum()

    st.write("Total Transactions:", len(df))
    st.write("Total Withdrawals:", total_withdrawals)

    # Save Excel
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")

    df.to_excel(temp_file.name, index=False)

    with open(temp_file.name, "rb") as f:
        st.download_button(
            "Download Clean Excel",
            f,
            "clean_statement.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )