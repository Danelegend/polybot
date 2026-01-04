from dataclasses import dataclass, field
from typing import Optional, Tuple

from polybot.common.enums import Side

@dataclass
class Level:
    price: float
    volume: float
    
    def __lt__(self, other: 'Level') -> bool:
        return self.price < other.price


@dataclass
class OrderBook:
    bids: list[Level] = field(default_factory=list)  # Descending order
    asks: list[Level] = field(default_factory=list)  # Ascending order
    
    def best_bid(self) -> Optional[Level]:
        return self.bids[0] if self.bids else None
    
    def best_ask(self) -> Optional[Level]:
        return self.asks[0] if self.asks else None
    
    def spread(self) -> float:
        """Returns the bid-ask spread, or 0 if book is incomplete"""
        bb, ba = self.best_bid(), self.best_ask()
        return (ba.price - bb.price) if (bb and ba) else 0.0
    
    def spread_bps(self) -> float:
        """Returns spread in basis points relative to midpoint"""
        mid = self.midpoint()
        return (self.spread() / mid * 10000) if mid > 0 else 0.0
    
    def midpoint(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        return ((bb.price + ba.price) / 2) if (bb and ba) else None
    
    def vwap(self, levels: int = 0) -> Optional[float]:
        """
        Calculate VWAP across first N levels of bids and asks.
        levels == 0 implies all levels.
        Returns None if orderbook is empty.
        """
        n = levels if levels > 0 else None
        bid_vol, bid_weighted = self._calculate_vwap_side(self.bids[:n])
        ask_vol, ask_weighted = self._calculate_vwap_side(self.asks[:n])
        
        total_vol = bid_vol + ask_vol
        if total_vol == 0:
            return None
        
        return (bid_weighted + ask_weighted) / total_vol
    
    def _calculate_vwap_side(self, levels: list[Level]) -> Tuple[float, float]:
        """Returns (total_volume, weighted_sum). Optimized iteration."""
        total_vol = sum(lvl.volume for lvl in levels)
        weighted_sum = sum(lvl.price * lvl.volume for lvl in levels)
        return total_vol, weighted_sum
    
    def depth(self, price: float, side: Side) -> float:
        """
        Calculate total volume available up to a given price.
        side: 'bid' or 'ask'
        """
        if side == Side.BUY:
            return sum(lvl.volume for lvl in self.bids if lvl.price >= price)
        else:
            return sum(lvl.volume for lvl in self.asks if lvl.price <= price)
    
    def impact_price(self, volume: float, side: Side) -> Optional[float]:
        """
        Calculate average execution price for a given volume.
        side: 'buy' (takes asks) or 'sell' (takes bids)
        Returns None if insufficient liquidity.
        """
        levels = self.asks if side == Side.BUY else self.bids
        remaining = volume
        weighted_sum = 0.0
        
        for lvl in levels:
            if remaining <= 0:
                break
            taken = min(remaining, lvl.volume)
            weighted_sum += taken * lvl.price
            remaining -= taken
        
        if remaining > 0:
            return None  # Insufficient liquidity
        
        return weighted_sum / volume
    
    def slippage(self, volume: float, side: Side) -> Optional[float]:
        """
        Calculate slippage in basis points for a given volume.
        Returns None if insufficient liquidity or no midpoint.
        """
        mid = self.midpoint()
        impact = self.impact_price(volume, side)
        
        if mid is None or impact is None or mid == 0:
            return None
        
        return abs(impact - mid) / mid * 10000
    
    def total_volume(self, levels: int = 0) -> Tuple[float, float]:
        """Returns (bid_volume, ask_volume) for first N levels"""
        n = levels if levels > 0 else None
        bid_vol = sum(lvl.volume for lvl in self.bids[:n])
        ask_vol = sum(lvl.volume for lvl in self.asks[:n])
        return bid_vol, ask_vol
    
    def imbalance(self, levels: int = 5) -> float:
        """
        Calculate order flow imbalance: (bid_vol - ask_vol) / (bid_vol + ask_vol)
        Returns value between -1 (all asks) and 1 (all bids)
        """
        bid_vol, ask_vol = self.total_volume(levels)
        total = bid_vol + ask_vol
        return ((bid_vol - ask_vol) / total) if total > 0 else 0.0
    
    def populate(self, bids: list[tuple[float, float]], asks: list[tuple[float, float]]):
        """
        Populate orderbook from raw data.
        Bids: list[(price, volume), ...] - will be sorted descending
        Asks: list[(price, volume), ...] - will be sorted ascending
        """
        self.bids = sorted([Level(p, v) for p, v in bids], reverse=True)
        self.asks = sorted([Level(p, v) for p, v in asks])
    
    def update_level(self, price: float, volume: float, side: Side):
        """
        Update or insert a single level. Removes level if volume == 0.
        side: 'bid' or 'ask'
        Maintains sorted order.
        """
        levels = self.bids if side == Side.BUY else self.asks
        reverse = (side == Side.BUY)
        
        # Find existing level
        for i, lvl in enumerate(levels):
            if lvl.price == price:
                if volume == 0:
                    levels.pop(i)
                else:
                    lvl.volume = volume
                return
        
        # Insert new level if volume > 0
        if volume > 0:
            new_level = Level(price, volume)
            if reverse:
                # For bids: insert in descending order
                for i, lvl in enumerate(levels):
                    if price > lvl.price:
                        levels.insert(i, new_level)
                        return
                levels.append(new_level)
            else:
                # For asks: insert in ascending order
                for i, lvl in enumerate(levels):
                    if price < lvl.price:
                        levels.insert(i, new_level)
                        return
                levels.append(new_level)
    
    def adjust_volume(self, price: float, volume_delta: float, side: Side) -> bool:
        """
        Add or subtract volume from an existing level.
        Returns True if level was found and adjusted, False otherwise.
        Removes level if resulting volume <= 0.
        
        Example:
            ob.adjust_volume(0.52, 100, 'bid')   # Add 100 to bid at 0.52
            ob.adjust_volume(0.52, -50, 'bid')   # Remove 50 from bid at 0.52
        """
        levels = self.bids if side == Side.BUY else self.asks
        
        for i, lvl in enumerate(levels):
            if lvl.price == price:
                new_volume = lvl.volume + volume_delta
                if new_volume <= 0:
                    levels.pop(i)
                else:
                    lvl.volume = new_volume
                return True
        
        return False
    
    def clear(self):
        """Clear all levels from the orderbook"""
        self.bids.clear()
        self.asks.clear()
    
    def __repr__(self) -> str:
        bb = self.best_bid()
        ba = self.best_ask()
        mid = self.midpoint()
        return (f"OrderBook(bid={bb.price if bb else None}, "
                f"ask={ba.price if ba else None}, "
                f"mid={mid}, spread={self.spread():.4f})")