# constants.py

DISCLAIMER_TEXT = """
หมายเหตุสำคัญ:
1) แหล่งอ้างอิงของข้อมูลที่ใช้ในการจำลอง:
   - ค่า mean (ผลตอบแทนเฉลี่ยรายปี) และ volatility (ความผันผวน) 
     ของสินทรัพย์ในระบบนี้เป็นค่า “ตัวอย่างเพื่อการศึกษา” (representative assumptions)
     โดยอิงจากข้อมูลเชิงสถิติระยะยาวที่พบในการศึกษาและบทวิเคราะห์ของสถาบันการเงินระดับโลก 
     เช่น Vanguard, BlackRock, Morningstar, และ MSCI 
     ไม่ใช่ค่าที่อ้างอิงถึงสินทรัพย์จริงใด ๆ เป็นการเฉพาะ

2) วิธีการคำนวณโดยสรุป:
   - ระบบใช้ Monte Carlo Simulation แบบสุ่มผลตอบแทนรายปีด้วยฟังก์ชัน random.gauss(mean, vol)
   - เงินออมปัจจุบัน (หลังหักเงินฉุกเฉิน) จะถูกแบ่งตามสัดส่วนพอร์ต (allocation)
   - เงินออมรายเดือนจะถูกแปลงเป็นเงินออมรายปีแล้วแบ่งเข้าสินทรัพย์ตามสัดส่วนพอร์ตเช่นกัน
   - ใช้ผลตอบแทนคาดหวัง (expected return) และความผันผวน (volatility) 
     เพื่อจำลองความเป็นไปได้ของมูลค่าพอร์ตในระยะยาว
   - ไม่มีการปรับพอร์ต (no rebalancing)
   - ไม่มีการปรับสัดส่วนพอร์ตตามอายุผู้ใช้
   - ไม่มีการใช้ข้อมูลราคาในตลาดจริงของประเทศไทย

3) สิ่งที่ “ยังไม่ได้พิจารณา” ในระบบเวอร์ชันนี้:
   - หนี้สิน การเปลี่ยนแปลงยอดหนี้ หรือดอกเบี้ยของหนี้ที่เพิ่มตามเวลา
   - การเพิ่มขึ้นของค่าใช้จ่ายในอนาคต
   - การเพิ่มขึ้นของรายได้ตามอายุงาน
   - การเปลี่ยนสัดส่วนทรัพย์สินระหว่างทาง (rebalancing)
   - ความเสี่ยงในตลาดจริงที่มี fat tails, black swans หรือ extreme events
   - ความสัมพันธ์ระหว่างสินทรัพย์ (correlation)
   - ภาษี ค่าธรรมเนียม ธรรมเนียมซื้อขาย หรือผลกระทบจาก FX exchange rate
   - การชะลอหรือหยุดการออมในบางช่วง
   - ผลกระทบจากเศรษฐกิจจริง หรือราคาสินทรัพย์เฉพาะตัวของบริษัทหรือกองทุนใด ๆ

ระบบนี้ถูกออกแบบเพื่อวัตถุประสงค์ทางการศึกษาเท่านั้น 
ไม่ใช่คำแนะนำด้านการลงทุน และไม่ควรนำไปใช้ประกอบการตัดสินใจทางการเงินจริง
"""


# Representative fictional asset types (mean annual return, annual volatility)
ASSET_PROFILES = {
    "CASH": {"label": "Cash / Bank Deposit", "mean": 0.01, "vol": 0.005},
    "BONDS": {"label": "Bonds (investment-grade)", "mean": 0.035, "vol": 0.04},
    "DOM_EQUITY": {"label": "Domestic Equity (representative)", "mean": 0.07, "vol": 0.16},
    "INT_EQUITY": {"label": "International Equity (representative)", "mean": 0.065, "vol": 0.15},
    "REITS": {"label": "REITs / Real Assets (representative)", "mean": 0.05, "vol": 0.12},
}

ALLOCATION_RULES = {
    "conservative": {"CASH": 0.30, "BONDS": 0.50, "DOM_EQUITY": 0.10, "INT_EQUITY": 0.05, "REITS": 0.05},
    "moderate":     {"CASH": 0.10, "BONDS": 0.40, "DOM_EQUITY": 0.30, "INT_EQUITY": 0.15, "REITS": 0.05},
    "aggressive":   {"CASH": 0.05, "BONDS": 0.20, "DOM_EQUITY": 0.45, "INT_EQUITY": 0.25, "REITS": 0.05},
}

# Defaults requested
DEFAULT_MONTE_CARLO_SIMS = 5000
DEFAULT_MAX_YEARS = 50
DEFAULT_INFLATION = 0.02  # 2%

# Heuristics
DEBT_SERVICE_RATIO_WARN = 0.35
MIN_EMERGENCY_MONTHS = 3
