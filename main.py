import yfinance as yf
from duckduckgo_search import DDGS
from transformers import pipeline
from fpdf import FPDF
import matplotlib.pyplot as plt
import pandas as pd
import datetime

# Initialize the summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

COMMON_TICKERS = {
   
}

class StockAgent:
    """Fetch stock data from Yahoo Finance."""

    @staticmethod
    def get_ticker_from_name(company_name):
        return COMMON_TICKERS.get(company_name.lower(), None)

    @staticmethod
    def get_stock_data(company_name):
        ticker = StockAgent.get_ticker_from_name(company_name)
        if not ticker:
            return {"error": f"Could not find ticker for '{company_name}'"}

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            history = stock.history(period="6mo")

            return {
                "company": company_name,
                "ticker": ticker,
                "history": history,
                "info": info
            }
        except Exception as e:
            return {"error": str(e)}

class NewsAgent:
    """Fetch latest financial news."""

    @staticmethod
    def get_financial_news(company_name):
        try:
            with DDGS() as ddgs:
                results = ddgs.text(company_name + " stock news", max_results=5)

            if not results:
                return {"error": "No relevant news found."}

            articles = "\n".join([res['body'] for res in results if res.get('body')])
            summary = summarizer(articles, max_length=100, min_length=30, do_sample=False)[0]['summary_text']

            return {
                "news": [{"title": res['title'], "url": res['href']} for res in results],
                "summary": summary
            }
        except Exception as e:
            return {"error": str(e)}

class PDFReport(FPDF):
    """Generates a well-formatted PDF report."""

    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(200, 10, "Financial Analysis Report", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_stock_info(self, stock_data):
        self.set_font("Arial", "B", 14)
        self.cell(200, 10, f"Stock Overview: {stock_data['company']} ({stock_data['ticker']})", ln=True)
        self.ln(5)

        self.set_font("Arial", size=12)
        stock_info = stock_data['info']
        table_data = [
            ["Market Cap", f"${stock_info.get('marketCap', 'N/A'):,}"],
            ["P/E Ratio", f"{stock_info.get('trailingPE', 'N/A')}"],
            ["Dividend Yield", f"{stock_info.get('dividendYield', 'N/A')}"],
            ["Revenue", f"${stock_info.get('totalRevenue', 'N/A'):,}"],
            ["52-Week High", f"${stock_info.get('fiftyTwoWeekHigh', 'N/A')}"],
            ["52-Week Low", f"${stock_info.get('fiftyTwoWeekLow', 'N/A')}"]
        ]

        for row in table_data:
            self.cell(60, 10, row[0], border=1)
            self.cell(60, 10, row[1], border=1, ln=True)
        self.ln(10)

    def add_news_section(self, news_data):
        self.set_font("Arial", "B", 14)
        self.cell(200, 10, "Latest Financial News", ln=True)
        self.ln(5)

        self.set_font("Arial", size=12)
        self.multi_cell(0, 10, f"Summary: {news_data['summary']}")
        self.ln(5)

        for article in news_data["news"]:
            self.set_text_color(0, 0, 255)
            self.cell(200, 10, f"{article['title']}", ln=True)
            self.cell(200, 10, article['url'], ln=True)
            self.ln(5)
        self.set_text_color(0, 0, 0)
        self.ln(10)

class FinancialAnalysis:
    """Runs financial analysis and generates a PDF report."""

    def __init__(self, company_name):
        self.company_name = company_name

    def run_analysis(self):
        stock_data = StockAgent.get_stock_data(self.company_name)
        news_data = NewsAgent.get_financial_news(self.company_name)

        return {"stock_analysis": stock_data, "news_analysis": news_data}

    def plot_graphs(self, history):
        plt.figure(figsize=(15, 10))

        # Closing Price Over Time
        plt.subplot(2, 2, 1)
        plt.plot(history.index, history['Close'], label="Close Price", color="blue")
        plt.title("Stock Price Over Time")
        plt.grid()

        # Moving Averages
        plt.subplot(2, 2, 2)
        history['SMA_50'] = history['Close'].rolling(window=50).mean()
        plt.plot(history.index, history['Close'], label="Close")
        plt.plot(history.index, history['SMA_50'], label="50-day SMA", linestyle="--")
        plt.title("Moving Averages")
        plt.legend()

        # Volume Trends
        plt.subplot(2, 2, 3)
        plt.bar(history.index, history['Volume'], color='purple')
        plt.title("Volume Trends")

        # Daily Returns
        plt.subplot(2, 2, 4)
        history['Daily Returns'] = history['Close'].pct_change() * 100
        plt.hist(history['Daily Returns'].dropna(), bins=30, color="green")
        plt.title("Daily Returns Distribution")

        plt.tight_layout()
        plt.savefig("financial_analysis.png")
        plt.close()

    def generate_pdf(self, analysis):
        """Create a structured and visually engaging PDF report."""
        pdf = PDFReport()
        pdf.add_page()

        pdf.add_stock_info(analysis["stock_analysis"])
        pdf.add_news_section(analysis["news_analysis"])

        self.plot_graphs(analysis["stock_analysis"]["history"])
        pdf.image("financial_analysis.png", x=10, w=180)

        pdf.output("Financial_Report.pdf")
        return "Financial_Report.pdf"

if __name__ == "__main__":
    company_name = input("Enter Company Name: ").strip()
    system = FinancialAnalysis(company_name)
    analysis = system.run_analysis()

    print("Generating PDF Report...")
    pdf_file = system.generate_pdf(analysis)
    print(f"PDF Report Generated: {pdf_file}")
