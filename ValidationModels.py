
from pydantic import BaseModel, field_validator
from datetime import datetime


class ExpenseInput(BaseModel):
    date: str
    amount: float
    category: str
    subcategory: str = ""
    note: str = ""

    @field_validator("date")
    @classmethod
    def normalize_date(cls, v):
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Invalid date '{v}'. Use DD-MM-YYYY or YYYY-MM-DD.")

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0.")
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Category cannot be empty.")
        return v.strip()


class DateRangeInput(BaseModel):
    start_date: str
    end_date: str
    
    @field_validator("start_date", "end_date")
    @classmethod
    def normalize_date(cls, v):
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Invalid date '{v}'. Use DD-MM-YYYY or YYYY-MM-DD.")

    def validate_range(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date.")


class SummarizeInput(DateRangeInput):
    category: str = ""