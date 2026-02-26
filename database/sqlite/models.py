from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ConfigWeldMachine(Base):
    __tablename__ = "WeldMachineConfig"

    id = Column(Integer, primary_key=True)   # id: str
    name = Column(String, nullable=False, unique=True)   # name: str

    volt_regs = Column(Integer, nullable=False)   # thanh ghi áp
    ampe_regs = Column(Integer, nullable=False)   # thanh ghi hàn
    resolution = Column(Integer, nullable=False)  # độ phân giải

    ampe_max = Column(Float, nullable=False)      # dòng tối đa
    ampe_min = Column(Float, nullable=False)      # dòng tối thiểu
    volt_max = Column(Float, nullable=False)      # áp tối đa
    volt_min = Column(Float, nullable=False)      # áp tối thiểu

    date_time = Column(DateTime, nullable=False)      # time: date

    def __repr__(self) -> str:
        return f"<ConfigWeldMachine id={self.id} name={self.name}>"
