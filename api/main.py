from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from analytics.db import engine


from ai.business_pipeline import BusinessPipeline


app = FastAPI(
    title="AI Business Intelligence API",
    description="Natural-language business analytics API powered by AI and PostgreSQL.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Business AI Pipeline
# ---------------------------------------------------------

pipeline = BusinessPipeline()


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------

class BusinessQuestion(BaseModel):
    question: str


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "AI Business Intelligence API",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/metrics")
def get_metrics():

    try:
        with engine.connect() as connection:

            revenue_result = connection.execute(
                text("""
                    SELECT COALESCE(SUM(total_amount), 0) AS revenue
                    FROM aibusinessanalytics.orders
                    WHERE order_date >= '2025-05-01'
                      AND order_date < '2025-06-01'
                """)
            ).mappings().first()

            orders_result = connection.execute(
                text("""
                    SELECT COUNT(*) AS orders
                    FROM aibusinessanalytics.orders
                    WHERE order_date >= '2025-05-01'
                      AND order_date < '2025-06-01'
                """)
            ).mappings().first()

            return_result = connection.execute(
                text("""
                    SELECT
                        COALESCE(
                            COUNT(DISTINCT r.order_id)::numeric
                            / NULLIF(COUNT(DISTINCT o.order_id), 0)
                            * 100,
                            0
                        ) AS return_rate
                    FROM aibusinessanalytics.orders o
                    LEFT JOIN aibusinessanalytics.returns r
                        ON r.order_id = o.order_id
                    WHERE o.order_date >= '2025-05-01'
                      AND o.order_date < '2025-06-01'
                """)
            ).mappings().first()

        return {
            "period": "May 2025",
            "revenue": float(revenue_result["revenue"]),
            "orders": int(orders_result["orders"]),
            "return_rate": float(return_result["return_rate"])
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

@app.get("/revenue-trend")
def get_revenue_trend():

    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT
                        TO_CHAR(DATE_TRUNC('month', order_date), 'Mon YYYY') AS month,
                        COALESCE(SUM(total_amount), 0) AS revenue
                    FROM aibusinessanalytics.orders
                    WHERE order_date >= '2025-04-01'
                      AND order_date < '2025-06-01'
                    GROUP BY DATE_TRUNC('month', order_date)
                    ORDER BY DATE_TRUNC('month', order_date)
                """)
            ).mappings().all()

        return {
            "data": [
                {
                    "month": row["month"],
                    "revenue": float(row["revenue"])
                }
                for row in result
            ]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


    
# ---------------------------------------------------------
# Ask business question
# ---------------------------------------------------------

@app.post("/ask")
def ask_business_question(
    request: BusinessQuestion
):

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = pipeline.ask(
            request.question
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )