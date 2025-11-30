# models.py
from pydantic import BaseModel, Field
from typing import Optional

class UserProfile(BaseModel):
    monthly_income: float = Field(..., ge=0, description="รายได้ต่อเดือน (บาท)")
    monthly_expense: float = Field(..., ge=0, description="ค่าใช้จ่ายต่อเดือน (รวมทุกอย่าง)")
    monthly_contribution: float = Field(..., ge=0, description="จำนวนเงินที่ต้องการใส่ในพอร์ตต่อเดือน")
    current_savings: float = Field(..., ge=0, description="ยอดเงินออมปัจจุบัน")
    emergency_fund_amount: Optional[float] = Field(None, ge=0, description="จำนวนเงินฉุกเฉินที่ต้องการเก็บไว้")
    emergency_fund_months: Optional[int] = Field(0, ge=0, description="จำนวนเดือนที่ต้องการเผื่อไว้เป็นเงินฉุกเฉิน")
    risk_bucket: Optional[str] = Field("moderate", description="ระดับความเสี่ยงของพอร์ต (conservative/moderate/aggressive)")
    current_cash_interest: Optional[float] = Field(0.01, description="อัตราดอกเบี้ยเงินฝากถ้าไม่ลงทุน (default = 1%)")
    inflation_rate: Optional[float] = Field(0.02, description="อัตราเงินเฟ้อที่ใช้ในการคำนวณ (default = 2%)")

class AnalysisRequest(BaseModel):
    profile: UserProfile
    target_amount: float = Field(..., gt=0, description="ยอดเงินเป้าหมาย (บาท)")
