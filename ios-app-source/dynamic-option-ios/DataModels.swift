//
//  DataModels.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import Foundation

// MARK: - Main Response Structure
struct OpportunitiesResponse: Codable {
    let opportunities: [OpportunityCard]
    let total_count: Int
}

// MARK: - Market Movers
struct MoversResponse: Codable {
    let gainers: [MoverStock]
    let losers: [MoverStock]
    let most_active: [MoverStock]
}

struct MoverStock: Codable, Identifiable, Hashable {
    var id: String { symbol }
    let symbol: String
    let name: String
    let price: Double
    let change_percent: Double
    let volume: Int
}


// MARK: - Opportunity Card
struct OpportunityCard: Codable, Identifiable, Hashable {
    let id: String
    let symbol: String
    let strategy_type: String
    let underlying_price: Double
    let max_profit: Double
    let win_rate: Double
    let dte: Int
    let ai_score: Double
    let expected_value: Double
    let liquidity_score: Double
    let rationale: String
    let legs: [OptionsLeg]
    let risk_metrics: StrategyMetrics

    // Conform to Hashable
    static func == (lhs: OpportunityCard, rhs: OpportunityCard) -> Bool {
        return lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - Options Leg
struct OptionsLeg: Codable, Identifiable, Hashable {
    var id = UUID()
    let symbol: String
    let option_type: String
    let strike: Double
    let expiration: String
    let quantity: Int
    let price: Double
    let delta: Double
    let theta: Double
    let vega: Double

    enum CodingKeys: String, CodingKey {
        case symbol, option_type, strike, expiration, quantity, price, delta, theta, vega
    }
    
    // Conform to Hashable
    static func == (lhs: OptionsLeg, rhs: OptionsLeg) -> Bool {
        return lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - Strategy Metrics
struct StrategyMetrics: Codable, Hashable {
    let max_profit: Double
    let max_loss: Double
    let breakeven_points: [Double]
    let profit_probability: Double
    let expected_return: Double
    let risk_reward_ratio: Double
    let total_delta: Double
    let total_theta: Double
    let total_vega: Double
    let capital_required: Double
}