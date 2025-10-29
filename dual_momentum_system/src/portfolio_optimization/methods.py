"""
Implementation of various portfolio optimization methods.
"""

from typing import Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform
from loguru import logger

from .base import PortfolioOptimizer, OptimizationResult


class EqualWeightOptimizer(PortfolioOptimizer):
    """
    Equal weight (1/N) portfolio.
    
    Simple but often surprisingly effective benchmark.
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Create equal weight portfolio.
        
        Args:
            returns: Asset returns DataFrame
            **kwargs: Ignored
        
        Returns:
            OptimizationResult with equal weights
        """
        self._validate_returns(returns)
        
        n_assets = len(returns.columns)
        weights = np.ones(n_assets) / n_assets
        weights = self._apply_constraints(weights)
        
        # Calculate metrics
        metrics = self._calculate_portfolio_metrics(weights, returns)
        
        return OptimizationResult(
            weights=dict(zip(returns.columns, weights)),
            method='equal_weight',
            expected_return=metrics['return'],
            expected_volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            diversification_ratio=metrics['diversification_ratio'],
            risk_contributions=dict(zip(returns.columns, metrics['risk_contributions'])),
        )


class InverseVolatilityOptimizer(PortfolioOptimizer):
    """
    Inverse volatility weighted portfolio.
    
    Weights assets inversely proportional to their volatility.
    Lower volatility assets get higher weights.
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Create inverse volatility weighted portfolio.
        
        Args:
            returns: Asset returns DataFrame
            **kwargs: Ignored
        
        Returns:
            OptimizationResult with inverse volatility weights
        """
        self._validate_returns(returns)
        
        # Calculate asset volatilities
        volatilities = returns.std()
        
        # Inverse volatility weights
        inv_vol = 1.0 / volatilities
        weights = inv_vol / inv_vol.sum()
        weights = self._apply_constraints(weights.values)
        
        # Calculate metrics
        metrics = self._calculate_portfolio_metrics(weights, returns)
        
        return OptimizationResult(
            weights=dict(zip(returns.columns, weights)),
            method='inverse_volatility',
            expected_return=metrics['return'],
            expected_volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            diversification_ratio=metrics['diversification_ratio'],
            risk_contributions=dict(zip(returns.columns, metrics['risk_contributions'])),
            metadata={'asset_volatilities': volatilities.to_dict()},
        )


class MinimumVarianceOptimizer(PortfolioOptimizer):
    """
    Minimum variance portfolio optimization.
    
    Finds the portfolio with the lowest possible volatility.
    Does not consider expected returns.
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Find minimum variance portfolio.
        
        Args:
            returns: Asset returns DataFrame
            **kwargs: Ignored
        
        Returns:
            OptimizationResult with minimum variance weights
        """
        self._validate_returns(returns)
        
        cov_matrix = returns.cov()
        n_assets = len(returns.columns)
        
        # Objective: minimize portfolio variance
        def portfolio_variance(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))
        
        # Constraints: weights sum to 1
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        
        # Bounds: min_weight <= w <= max_weight
        bounds = tuple((self.min_weight, self.max_weight) for _ in range(n_assets))
        
        # Initial guess: equal weights
        initial_weights = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            portfolio_variance,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        weights = result.x
        
        # Calculate metrics
        metrics = self._calculate_portfolio_metrics(weights, returns, cov_matrix)
        
        return OptimizationResult(
            weights=dict(zip(returns.columns, weights)),
            method='minimum_variance',
            expected_return=metrics['return'],
            expected_volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            diversification_ratio=metrics['diversification_ratio'],
            risk_contributions=dict(zip(returns.columns, metrics['risk_contributions'])),
            metadata={'converged': result.success, 'iterations': result.nit},
        )


class MaximumSharpeOptimizer(PortfolioOptimizer):
    """
    Maximum Sharpe ratio portfolio optimization.
    
    Finds the portfolio with the highest risk-adjusted return.
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Find maximum Sharpe ratio portfolio.
        
        Args:
            returns: Asset returns DataFrame
            **kwargs: Ignored
        
        Returns:
            OptimizationResult with maximum Sharpe weights
        """
        self._validate_returns(returns)
        
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        n_assets = len(returns.columns)
        
        # Objective: maximize Sharpe ratio (minimize negative Sharpe)
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            if portfolio_volatility == 0:
                return np.inf
            
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_volatility
            return -sharpe
        
        # Constraints: weights sum to 1
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        
        # Bounds: min_weight <= w <= max_weight
        bounds = tuple((self.min_weight, self.max_weight) for _ in range(n_assets))
        
        # Initial guess: equal weights
        initial_weights = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            negative_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        weights = result.x
        
        # Calculate metrics
        metrics = self._calculate_portfolio_metrics(weights, returns, cov_matrix)
        
        return OptimizationResult(
            weights=dict(zip(returns.columns, weights)),
            method='maximum_sharpe',
            expected_return=metrics['return'],
            expected_volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            diversification_ratio=metrics['diversification_ratio'],
            risk_contributions=dict(zip(returns.columns, metrics['risk_contributions'])),
            metadata={'converged': result.success, 'iterations': result.nit},
        )


class RiskParityOptimizer(PortfolioOptimizer):
    """
    Risk parity portfolio optimization.
    
    Equalizes risk contribution from each asset.
    Each asset contributes the same amount to portfolio volatility.
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Find risk parity portfolio.
        
        Args:
            returns: Asset returns DataFrame
            **kwargs: Ignored
        
        Returns:
            OptimizationResult with risk parity weights
        """
        self._validate_returns(returns)
        
        cov_matrix = returns.cov()
        n_assets = len(returns.columns)
        
        # Target risk contribution: equal for all assets
        target_risk = np.ones(n_assets) / n_assets
        
        # Objective: minimize difference from target risk contributions
        def risk_budget_objective(weights):
            # Portfolio volatility
            portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_vol = np.sqrt(portfolio_var)
            
            if portfolio_vol == 0:
                return np.inf
            
            # Marginal risk contribution
            marginal_contrib = np.dot(cov_matrix, weights)
            
            # Risk contribution
            risk_contrib = weights * marginal_contrib / portfolio_vol
            
            # Normalize risk contributions
            risk_contrib_pct = risk_contrib / np.sum(risk_contrib)
            
            # Sum of squared differences from target
            return np.sum((risk_contrib_pct - target_risk) ** 2)
        
        # Constraints: weights sum to 1, all positive
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        
        # Bounds: min_weight <= w <= max_weight
        bounds = tuple((max(self.min_weight, 0.001), self.max_weight) for _ in range(n_assets))
        
        # Initial guess: inverse volatility (close to risk parity)
        volatilities = np.sqrt(np.diag(cov_matrix))
        initial_weights = (1.0 / volatilities) / np.sum(1.0 / volatilities)
        
        # Optimize
        result = minimize(
            risk_budget_objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        weights = result.x
        
        # Calculate metrics
        metrics = self._calculate_portfolio_metrics(weights, returns, cov_matrix)
        
        return OptimizationResult(
            weights=dict(zip(returns.columns, weights)),
            method='risk_parity',
            expected_return=metrics['return'],
            expected_volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            diversification_ratio=metrics['diversification_ratio'],
            risk_contributions=dict(zip(returns.columns, metrics['risk_contributions'])),
            metadata={'converged': result.success, 'iterations': result.nit},
        )


class MaximumDiversificationOptimizer(PortfolioOptimizer):
    """
    Maximum diversification portfolio optimization.
    
    Maximizes the diversification ratio:
    (weighted average of individual volatilities) / (portfolio volatility)
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Find maximum diversification portfolio.
        
        Args:
            returns: Asset returns DataFrame
            **kwargs: Ignored
        
        Returns:
            OptimizationResult with maximum diversification weights
        """
        self._validate_returns(returns)
        
        cov_matrix = returns.cov()
        volatilities = np.sqrt(np.diag(cov_matrix))
        n_assets = len(returns.columns)
        
        # Objective: maximize diversification ratio (minimize negative ratio)
        def negative_diversification_ratio(weights):
            portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_vol = np.sqrt(portfolio_var)
            
            if portfolio_vol == 0:
                return np.inf
            
            weighted_vol = np.dot(weights, volatilities)
            div_ratio = weighted_vol / portfolio_vol
            
            return -div_ratio
        
        # Constraints: weights sum to 1
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
        
        # Bounds: min_weight <= w <= max_weight
        bounds = tuple((self.min_weight, self.max_weight) for _ in range(n_assets))
        
        # Initial guess: inverse volatility
        initial_weights = (1.0 / volatilities) / np.sum(1.0 / volatilities)
        
        # Optimize
        result = minimize(
            negative_diversification_ratio,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        weights = result.x
        
        # Calculate metrics
        metrics = self._calculate_portfolio_metrics(weights, returns, cov_matrix)
        
        return OptimizationResult(
            weights=dict(zip(returns.columns, weights)),
            method='maximum_diversification',
            expected_return=metrics['return'],
            expected_volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            diversification_ratio=metrics['diversification_ratio'],
            risk_contributions=dict(zip(returns.columns, metrics['risk_contributions'])),
            metadata={'converged': result.success, 'iterations': result.nit},
        )


class HierarchicalRiskParityOptimizer(PortfolioOptimizer):
    """
    Hierarchical Risk Parity (HRP) portfolio optimization.
    
    Machine learning approach using hierarchical clustering.
    Developed by Marcos López de Prado.
    
    Steps:
    1. Compute distance matrix from correlation matrix
    2. Perform hierarchical clustering
    3. Quasi-diagonalize covariance matrix
    4. Recursively bisect and allocate weights
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        Find HRP portfolio.
        
        Args:
            returns: Asset returns DataFrame
            **kwargs: Can include 'linkage_method' (default: 'single')
        
        Returns:
            OptimizationResult with HRP weights
        """
        self._validate_returns(returns)
        
        linkage_method = kwargs.get('linkage_method', 'single')
        
        # Step 1: Compute correlation and distance matrices
        corr_matrix = returns.corr()
        distance_matrix = np.sqrt(0.5 * (1 - corr_matrix))
        
        # Step 2: Hierarchical clustering
        dist_condensed = squareform(distance_matrix, checks=False)
        link = linkage(dist_condensed, method=linkage_method)
        
        # Step 3: Quasi-diagonalization (get optimal leaf order)
        sorted_indices = self._get_quasi_diag(link, len(returns.columns))
        
        # Step 4: Recursive bisection
        cov_matrix = returns.cov()
        weights = self._recursive_bisection(cov_matrix, sorted_indices)
        
        # Reorder weights to match original column order
        weights_reordered = np.zeros(len(returns.columns))
        for i, idx in enumerate(sorted_indices):
            weights_reordered[idx] = weights[i]
        
        weights = self._apply_constraints(weights_reordered)
        
        # Calculate metrics
        metrics = self._calculate_portfolio_metrics(weights, returns, cov_matrix)
        
        return OptimizationResult(
            weights=dict(zip(returns.columns, weights)),
            method='hierarchical_risk_parity',
            expected_return=metrics['return'],
            expected_volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            diversification_ratio=metrics['diversification_ratio'],
            risk_contributions=dict(zip(returns.columns, metrics['risk_contributions'])),
            metadata={'linkage_method': linkage_method},
        )
    
    def _get_quasi_diag(self, link, n_assets):
        """Get quasi-diagonal order from linkage matrix."""
        # Get clusters at each level
        clusters = [[i] for i in range(n_assets)]
        
        for i in range(len(link)):
            clusters.append(clusters[int(link[i, 0])] + clusters[int(link[i, 1])])
        
        # Return the final cluster (optimal order)
        return clusters[-1]
    
    def _recursive_bisection(self, cov_matrix, sorted_indices):
        """Recursively bisect clusters and allocate weights."""
        weights = np.ones(len(sorted_indices))
        
        def bisect(indices):
            if len(indices) == 1:
                return
            
            # Split cluster in half
            mid = len(indices) // 2
            left_indices = indices[:mid]
            right_indices = indices[mid:]
            
            # Calculate cluster variances
            left_var = self._cluster_variance(cov_matrix, left_indices)
            right_var = self._cluster_variance(cov_matrix, right_indices)
            
            # Allocate weights inversely proportional to variance
            total_var = left_var + right_var
            left_weight = 1.0 - left_var / total_var
            right_weight = 1.0 - right_var / total_var
            
            # Normalize
            total = left_weight + right_weight
            left_weight /= total
            right_weight /= total
            
            # Update weights
            for idx in left_indices:
                weights[sorted_indices.index(idx)] *= left_weight
            for idx in right_indices:
                weights[sorted_indices.index(idx)] *= right_weight
            
            # Recurse
            bisect(left_indices)
            bisect(right_indices)
        
        bisect(sorted_indices)
        return weights
    
    def _cluster_variance(self, cov_matrix, indices):
        """Calculate variance of a cluster."""
        if len(indices) == 1:
            return cov_matrix[indices[0], indices[0]]
        
        # Equal weight within cluster
        weights = np.ones(len(indices)) / len(indices)
        
        # Cluster covariance submatrix
        cluster_cov = cov_matrix[np.ix_(indices, indices)]
        
        # Cluster variance
        return np.dot(weights, np.dot(cluster_cov, weights))
