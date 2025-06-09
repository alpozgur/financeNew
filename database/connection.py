from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import pandas as pd
from typing import Optional, Dict, List
import logging
from config.config import Config

Base = declarative_base()

class DatabaseManager:
    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.Session = None
        self.logger = logging.getLogger(__name__)
        self._initialize_connection()

    def _initialize_connection(self):
        try:
            self.engine = create_engine(
                self.config.database.connection_string,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
            self.Session = sessionmaker(bind=self.engine)
            self.logger.info("Database connection successful")
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise

        # with self.engine.connect()

    def format_query_params(self, query: str, params=None) -> tuple:
        """
        Query ve parametreleri PostgreSQL formatına çevir
        
        Returns:
            tuple: (formatted_query, formatted_params)
        """
        if not params:
            return query, None
        
        # Eğer string formatting kullanılıyorsa, güvenli bir şekilde çevir
        if isinstance(params, dict):
            # :param → %(param)s dönüşümü
            formatted_query = query
            for key in params.keys():
                formatted_query = formatted_query.replace(f':{key}', f'%({key})s')
            return formatted_query, params
            
        elif isinstance(params, (list, tuple)):
            # Positional parametreler - PostgreSQL array syntax kullan
            formatted_query = query
            placeholders = []
            for i, _ in enumerate(params):
                placeholders.append(f'${i+1}')
            
            # %s'leri $1, $2, ... ile değiştir
            for placeholder in placeholders:
                formatted_query = formatted_query.replace('%s', placeholder, 1)
                
            return formatted_query, params
        
        return query, params

    # Kullanım:
    def execute_query(self, query: str, params=None) -> pd.DataFrame:
        """SQL sorgusunu çalıştır"""
        formatted_query, formatted_params = self.format_query_params(query, params)
        
        try:
            with self.engine.connect() as conn:
                if formatted_params:
                    return pd.read_sql_query(formatted_query, conn, params=formatted_params)
                else:
                    return pd.read_sql_query(formatted_query, conn)
        except Exception as e:
            print(f"Query execution error: {e}")
            raise e
    # --- TEFASFUNDS ---

    def get_fund_data(self, 
                     fcode: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     limit: Optional[int] = None) -> pd.DataFrame:
        """Get fund data from tefasfunds"""
        query = """
        SELECT idtefas, pdate, price, fcode, ftitle, 
               fcapacity, sharecount, investorcount
        FROM tefasfunds
        WHERE 1=1 and investorcount>10
        """
        params = {}
        if fcode:
            query += " AND fcode = :fcode"
            params['fcode'] = fcode
        if start_date:
            query += " AND pdate >= :start_date"
            params['start_date'] = start_date
        if end_date:
            query += " AND pdate <= :end_date"
            params['end_date'] = end_date
        query += " ORDER BY pdate DESC"
        if limit:
            query += f" LIMIT {limit}"
        return self.execute_query(query, params)

    def get_all_fund_codes(self) -> List[str]:
        query = "SELECT DISTINCT fcode FROM tefasfunds WHERE 1=1 and investorcount>10 ORDER BY fcode"
        result = self.execute_query(query)
        return result['fcode'].tolist()

    def get_fund_price_history(self, fund_code, days=30):
        """Fonun fiyat geçmişini al - PostgreSQL format fix"""
        query = """
        SELECT pdate, price, fcode
        FROM tefasfunds
        WHERE fcode = %(fcode)s and investorcount>10
        ORDER BY pdate DESC
        LIMIT %(days)s
        """
        params = {'fcode': fund_code, 'days': days}
        result = self.execute_query(query, params)
        return result
    # --- TEFAS_FUNDDETAILS ---

    def get_fund_details(self, fcode: str) -> dict:
        """
        Get detailed information for a given fund code from tefas_funddetails.
        Returns all available columns.
        """
        query = """
        SELECT * FROM tefasfunddetails
        WHERE fcode = :fcode
        LIMIT 1
        """
        result = self.execute_query(query, {"fcode": fcode})
        if result.empty:
            return {}
        return result.iloc[0].to_dict()

    def get_all_fund_details(self) -> pd.DataFrame:
        """List all funds from tefasfunddetails"""
        query = """
        SELECT * FROM tefasfunddetails
        ORDER BY fcode
        """
        return self.execute_query(query)

    def get_funds_with_details(self, 
                              bankbills: Optional[bool] = None, 
                              ftype: Optional[str] = None) -> pd.DataFrame:
        """
        Get all funds with optional filters.
        bankbills, ftype gibi istediğin kolona göre filtre ekleyebilirsin.
        """
        query = """
        SELECT * FROM tefasfunddetails
        WHERE 1=1
        """
        params = {}
        if bankbills is not None:
            query += " AND bankbills = :bankbills"
            params["bankbills"] = int(bankbills)
        if ftype:
            query += " AND ftype = :ftype"
            params["ftype"] = ftype
        query += " ORDER BY fcode"
        return self.execute_query(query, params)

    def get_fund_full_history_with_details(self, fcode: str, limit: int = 365) -> pd.DataFrame:
        """
        Join tefasfunds and tefasfunddetails for full fund history + details.
        """
        query = """
        SELECT f.*, d.*
        FROM tefasfunds f
        LEFT JOIN tefasfunddetails d ON f.fcode = d.fcode
        WHERE f.fcode = :fcode and investorcount>10
        ORDER BY f.pdate DESC
        LIMIT :limit
        """
        params = {"fcode": fcode, "limit": limit}
        return self.execute_query(query, params)

    # --- TEFAS_DESCRIPTIONS ---

    def get_fund_descriptions(self, fcode: str, limit: int = 5) -> pd.DataFrame:
        """
        Get last N descriptions for a fund from tefas_descriptions
        """
        query = """
        SELECT * FROM tefas_descriptions
        WHERE fcode = :fcode
        ORDER BY pdate DESC
        LIMIT :limit
        """
        params = {"fcode": fcode, "limit": limit}
        return self.execute_query(query, params)
