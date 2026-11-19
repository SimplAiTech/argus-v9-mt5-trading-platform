"""ARGUS Vision - Калькулятор метрик

Функции для расчета торговых метрик:
- Win Rate, Profit Factor
- Sharpe/Sortino Ratio
- Max Drawdown
- R-кратность
- MFE/MAE
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from .logger import get_logger

logger = get_logger(__name__)


class MetricsCalculator:
    """Калькулятор торговых метрик
    
    Предоставляет статические методы для расчета
    различных торговых показателей.
    """
    
    @staticmethod
    def win_rate(trades: List[Dict]) -> float:
        """Расчет Win Rate
        
        Args:
            trades: Список сделок с полем 'profit' или 'pnl'
            
        Returns:
            Win Rate в процентах (0-100)
        """
        if not trades:
            return 0.0
        
        winners = sum(1 for t in trades 
                     if float(t.get('profit', t.get('pnl', 0))) > 0)
        return (winners / len(trades)) * 100
    
    @staticmethod
    def profit_factor(trades: List[Dict]) -> float:
        """Расчет Profit Factor
        
        Args:
            trades: Список сделок с полем 'profit' или 'pnl'
            
        Returns:
            Profit Factor (gross_profit / gross_loss)
        """
        if not trades:
            return 0.0
        
        gross_profit = sum(float(t.get('profit', t.get('pnl', 0))) 
                         for t in trades 
                         if float(t.get('profit', t.get('pnl', 0))) > 0)
        gross_loss = abs(sum(float(t.get('profit', t.get('pnl', 0))) 
                            for t in trades 
                            if float(t.get('profit', t.get('pnl', 0))) < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    @staticmethod
    def total_pnl(trades: List[Dict]) -> float:
        """Расчет общего PnL
        
        Args:
            trades: Список сделок
            
        Returns:
            Общий PnL
        """
        return sum(float(t.get('profit', t.get('pnl', 0))) for t in trades)
    
    @staticmethod
    def average_pnl(trades: List[Dict]) -> float:
        """Средний PnL на сделку
        
        Args:
            trades: Список сделок
            
        Returns:
            Средний PnL
        """
        if not trades:
            return 0.0
        return MetricsCalculator.total_pnl(trades) / len(trades)
    
    @staticmethod
    def average_winner(trades: List[Dict]) -> float:
        """Средняя прибыльная сделка
        
        Args:
            trades: Список сделок
            
        Returns:
            Средняя прибыль выигрышной сделки
        """
        winners = [float(t.get('profit', t.get('pnl', 0))) 
                  for t in trades 
                  if float(t.get('profit', t.get('pnl', 0))) > 0]
        return np.mean(winners) if winners else 0.0
    
    @staticmethod
    def average_loser(trades: List[Dict]) -> float:
        """Средняя убыточная сделка
        
        Args:
            trades: Список сделок
            
        Returns:
            Средний убыток (отрицательное число)
        """
        losers = [float(t.get('profit', t.get('pnl', 0))) 
                 for t in trades 
                 if float(t.get('profit', t.get('pnl', 0))) < 0]
        return np.mean(losers) if losers else 0.0
    
    @staticmethod
    def average_rr(trades: List[Dict]) -> float:
        """Средний Risk:Reward
        
        Args:
            trades: Список сделок
            
        Returns:
            Средний R:R
        """
        avg_win = abs(MetricsCalculator.average_winner(trades))
        avg_loss = abs(MetricsCalculator.average_loser(trades))
        
        if avg_loss == 0:
            return 0.0
        
        return avg_win / avg_loss
    
    @staticmethod
    def max_drawdown(equity_curve: List[float]) -> Tuple[float, float]:
        """Расчет максимальной просадки
        
        Args:
            equity_curve: Кривая эквити (список значений)
            
        Returns:
            Tuple (max_drawdown_value, max_drawdown_pct)
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0, 0.0
        
        equity = np.array(equity_curve)
        peak = equity[0]
        max_dd = 0.0
        max_dd_pct = 0.0
        
        for value in equity:
            if value > peak:
                peak = value
            dd = peak - value
            dd_pct = (dd / peak) * 100 if peak > 0 else 0
            
            if dd > max_dd:
                max_dd = dd
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
        
        return max_dd, max_dd_pct
    
    @staticmethod
    def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0,
                    periods_per_year: int = 252) -> float:
        """Расчет Sharpe Ratio
        
        Args:
            returns: Список доходностей (дневных/периодических)
            risk_free_rate: Безрисковая ставка (годовая)
            periods_per_year: Количество периодов в году
            
        Returns:
            Sharpe Ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_arr = np.array(returns)
        excess_returns = returns_arr - (risk_free_rate / periods_per_year)
        
        mean_return = np.mean(excess_returns)
        std_return = np.std(excess_returns, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Аннуализированный Sharpe
        return (mean_return / std_return) * np.sqrt(periods_per_year)
    
    @staticmethod
    def sortino_ratio(returns: List[float], risk_free_rate: float = 0.0,
                     periods_per_year: int = 252) -> float:
        """Расчет Sortino Ratio
        
        Args:
            returns: Список доходностей
            risk_free_rate: Безрисковая ставка
            periods_per_year: Количество периодов в году
            
        Returns:
            Sortino Ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_arr = np.array(returns)
        excess_returns = returns_arr - (risk_free_rate / periods_per_year)
        
        mean_return = np.mean(excess_returns)
        
        # Только отрицательные отклонения
        negative_returns = excess_returns[excess_returns < 0]
        if len(negative_returns) == 0:
            return float('inf') if mean_return > 0 else 0.0
        
        downside_std = np.std(negative_returns, ddof=1)
        
        if downside_std == 0:
            return 0.0
        
        return (mean_return / downside_std) * np.sqrt(periods_per_year)
    
    @staticmethod
    def r_multiple(entry_price: float, exit_price: float, 
                  sl_price: float, position_type: str) -> float:
        """Расчет R-кратности сделки
        
        Args:
            entry_price: Цена входа
            exit_price: Цена выхода
            sl_price: Цена Stop Loss
            position_type: Тип позиции (BUY/SELL)
            
        Returns:
            R-кратность
        """
        initial_risk = abs(entry_price - sl_price)
        
        if initial_risk == 0:
            return 0.0
        
        if position_type == 'BUY':
            profit = exit_price - entry_price
        else:  # SELL
            profit = entry_price - exit_price
        
        return profit / initial_risk
    
    @staticmethod
    def expected_value(win_rate: float, avg_winner: float, 
                      avg_loser: float) -> float:
        """Расчет Expected Value (математическое ожидание)
        
        Args:
            win_rate: Win Rate в процентах (0-100)
            avg_winner: Средняя прибыль
            avg_loser: Средний убыток (отрицательное число)
            
        Returns:
            Expected Value на сделку
        """
        win_prob = win_rate / 100
        loss_prob = 1 - win_prob
        
        return (win_prob * avg_winner) + (loss_prob * avg_loser)
    
    @staticmethod
    def consecutive_wins_losses(trades: List[Dict]) -> Tuple[int, int]:
        """Максимальные серии побед и поражений
        
        Args:
            trades: Список сделок
            
        Returns:
            Tuple (max_consecutive_wins, max_consecutive_losses)
        """
        if not trades:
            return 0, 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            pnl = float(trade.get('profit', trade.get('pnl', 0)))
            
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif pnl < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            # pnl == 0 - breakeven, не влияет на серию
        
        return max_wins, max_losses
    
    @staticmethod
    def mfe_mae_efficiency(mfe: float, mae: float) -> float:
        """Расчет эффективности MFE/MAE
        
        Показывает насколько хорошо сделка использовала
        потенциальную прибыль относительно максимального риска.
        
        Args:
            mfe: Maximum Favorable Excursion
            mae: Maximum Adverse Excursion
            
        Returns:
            Коэффициент эффективности
        """
        if mae == 0:
            return float('inf') if mfe > 0 else 0.0
        
        return mfe / mae
    
    @staticmethod
    def average_trade_duration(trades: List[Dict]) -> float:
        """Средняя продолжительность сделки в минутах
        
        Args:
            trades: Список сделок с полями entry_time и exit_time
            
        Returns:
            Средняя продолжительность в минутах
        """
        durations = []
        
        for trade in trades:
            entry = trade.get('entry_time')
            exit_t = trade.get('exit_time', trade.get('close_time'))
            
            if entry and exit_t:
                try:
                    if isinstance(entry, str):
                        entry = datetime.fromisoformat(entry.replace('Z', '+00:00'))
                    if isinstance(exit_t, str):
                        exit_t = datetime.fromisoformat(exit_t.replace('Z', '+00:00'))
                    
                    duration = (exit_t - entry).total_seconds() / 60
                    durations.append(duration)
                except Exception:
                    pass
        
        return np.mean(durations) if durations else 0.0
    
    @staticmethod
    def calculate_all_metrics(trades: List[Dict]) -> Dict:
        """Расчет всех метрик для набора сделок
        
        Args:
            trades: Список сделок
            
        Returns:
            Словарь со всеми метриками
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_pnl': 0.0,
                'average_pnl': 0.0,
                'average_winner': 0.0,
                'average_loser': 0.0,
                'average_rr': 0.0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'expected_value': 0.0
            }
        
        winners = [t for t in trades 
                  if float(t.get('profit', t.get('pnl', 0))) > 0]
        losers = [t for t in trades 
                 if float(t.get('profit', t.get('pnl', 0))) < 0]
        
        win_rate = MetricsCalculator.win_rate(trades)
        avg_winner = MetricsCalculator.average_winner(trades)
        avg_loser = MetricsCalculator.average_loser(trades)
        max_wins, max_losses = MetricsCalculator.consecutive_wins_losses(trades)
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winners),
            'losing_trades': len(losers),
            'breakeven_trades': len(trades) - len(winners) - len(losers),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(MetricsCalculator.profit_factor(trades), 2),
            'total_pnl': round(MetricsCalculator.total_pnl(trades), 2),
            'average_pnl': round(MetricsCalculator.average_pnl(trades), 2),
            'average_winner': round(avg_winner, 2),
            'average_loser': round(avg_loser, 2),
            'average_rr': round(MetricsCalculator.average_rr(trades), 2),
            'max_consecutive_wins': max_wins,
            'max_consecutive_losses': max_losses,
            'expected_value': round(
                MetricsCalculator.expected_value(win_rate, avg_winner, avg_loser), 2
            ),
            'avg_trade_duration_minutes': round(
                MetricsCalculator.average_trade_duration(trades), 0
            )
        }
    
    @staticmethod
    def performance_by_group(trades: List[Dict], group_field: str) -> Dict[str, Dict]:
        """Расчет метрик с группировкой по полю
        
        Args:
            trades: Список сделок
            group_field: Поле для группировки (strategy_id, session, etc.)
            
        Returns:
            Словарь {group_value: metrics}
        """
        groups = {}
        
        for trade in trades:
            group = trade.get(group_field, 'UNKNOWN')
            if group not in groups:
                groups[group] = []
            groups[group].append(trade)
        
        return {
            group: MetricsCalculator.calculate_all_metrics(group_trades)
            for group, group_trades in groups.items()
        }
