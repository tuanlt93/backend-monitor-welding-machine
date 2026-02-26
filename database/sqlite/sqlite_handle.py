from __future__ import annotations
from typing import Iterable, Optional, List, Tuple
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.sqlite.models import Base, ConfigWeldMachine
from utils.logger import Logger
from utils.pattern import Singleton

class SqliteHandle(metaclass=Singleton):
    """
    Repository class quản lý CRUD cho bảng ConfigWeldMachine.
    """
    def __init__(self, *args, **kwargs) -> None:
        self.__db_url = kwargs.get('url', "sqlite:///ConfigWeldMachine.db")
        self.__engine = create_engine(self.__db_url, echo= False, future= True)
        Base.metadata.create_all(self.__engine)
        # expire_on_commit=False để object vẫn giữ giá trị sau commit
        self.Session = sessionmaker(bind=self.__engine, expire_on_commit=False, future=True)

        Logger().info("SQLITE READY")

    # ---------------------------
    # Create / Add
    # ---------------------------
    def add(
        self,
        *,
        id: int,
        name: str,
        volt_regs: int,
        ampe_regs: int,
        resolution: int,
        volt_max: float,
        volt_min: float,
        ampe_max: float,
        ampe_min: float
    ) -> Tuple[bool, Optional[str]]:
        """
        """
        rec = ConfigWeldMachine(
            id=id,
            name=name,
            volt_regs=volt_regs,
            ampe_regs=ampe_regs,
            resolution=resolution,
            volt_max=volt_max,
            volt_min=volt_min,
            ampe_max=ampe_max,
            ampe_min=ampe_min,
            date_time=datetime.now()
        )

        with self.Session() as s:
            try:
                if s.get(ConfigWeldMachine, id) is not None:
                    return False, "ID đã được sử dụng"
                if s.query(ConfigWeldMachine).filter_by(name=name).first() is not None:
                    return False, "Tên đã được sử dụng"
                s.add(rec)
                s.commit()
                return True, "Tạo mới thành công"
            except Exception as e:
                s.rollback()
                return False, f"Lỗi khác: {e}"
    
    def __to_dict(self, rec: ConfigWeldMachine):
        return {
            "id": rec.id,
            "name": rec.name,
            "volt_regs": rec.volt_regs,
            "ampe_regs": rec.ampe_regs,
            "resolution": rec.resolution,
            "ampe_max": rec.ampe_max,
            "ampe_min": rec.ampe_min,
            "volt_max": rec.volt_max,
            "volt_min": rec.volt_min,
        }

    def add_many(self, records: Iterable[ConfigWeldMachine]) -> List[ConfigWeldMachine]:
        """
            Thêm nhiều bản ghi (khi bạn đã tự tạo object ConfigWeldMachine).
            Chưa có check tùng ID và name
        """
        with self.Session() as s:
            s.add_all(list(records))
            s.commit()
            # Không refresh từng cái cho nhanh; nếu cần có thể loop s.refresh()
            return list(records)

    def get_all(self) -> list[dict]:
        """
            Lấy tất cả bản ghi
        """
        with self.Session() as s:
            records: List[ConfigWeldMachine] = s.query(ConfigWeldMachine).all()
            return [self.__to_dict(rec) for rec in records]

    def get_by_id(self, id: str) -> dict:
        """
            Lấy bản ghi thoe id
        """
        with self.Session() as s:
            rec: Optional[ConfigWeldMachine] = s.get(ConfigWeldMachine, id)
            if not rec:
                return {}
            return self.__to_dict(rec)

    def delete_by_id(self, id: str) -> int:
        """
        Xoá theo id.
        Return: số bản ghi bị xoá (0 hoặc 1).
        """
        with self.Session() as s:
            rec = s.get(ConfigWeldMachine, id)
            if not rec:
                return 0
            s.delete(rec)
            s.commit()
            return 1

    def delete_all(self) -> int:
        """
        Xoá tất cả bản ghi trong bảng.
        Return: số bản ghi bị xoá.
        """
        with self.Session() as s:
            # SQLAlchemy ORM delete() trên Query
            count = s.query(ConfigWeldMachine).delete()  # type: ignore[arg-type]
            s.commit()
            return int(count)


    def edit_by_name(self,
            *,
            id: int,
            name: str,
            volt_regs: int,
            ampe_regs: int,
            resolution: int,
            volt_max: float,
            volt_min: float,
            ampe_max: float,
            ampe_min: float
        ) -> Tuple[bool, Optional[str]]:

        """
            Cập nhật bản ghi theo name. Chỉ cập nhật các field hợp lệ.
        """

        update_data = {
            "volt_regs": volt_regs,
            "ampe_regs": ampe_regs,
            "resolution": resolution,
            "ampe_max": ampe_max,
            "ampe_min": ampe_min,
            "volt_max": volt_max,
            "volt_min": volt_min,
            "date_time": datetime.now()
        }
        for key, value in update_data.items():
            if value is None:
                return False, "Dữ liệu cập nhật sai"

        with self.Session() as s:
            rec = s.query(ConfigWeldMachine).filter_by(name=name).first()
            if not rec:
                return False, f"Không tìm thấy {name}"

            for key, value in update_data.items():
                setattr(rec, key, value)

            try:
                s.commit()
                return True, "Cập nhật thành công"
            except Exception as e:
                s.rollback()
                return False, f"Lỗi khác: {e}"