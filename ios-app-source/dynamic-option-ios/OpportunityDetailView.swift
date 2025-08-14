//
//  OpportunityDetailView.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import SwiftUI

struct OpportunityDetailView: View {
    let opportunity: OpportunityCard
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                
                // Header
                VStack(alignment: .leading, spacing: 8) {
                    Text(opportunity.symbol)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    Text(opportunity.strategy_type.replacingOccurrences(of: "_", with: " ").capitalized)
                        .font(.title2)
                        .foregroundColor(.secondary)
                }
                
                // AI Rationale
                VStack(alignment: .leading, spacing: 8) {
                    Text("AI Rationale")
                        .font(.headline)
                    Text(opportunity.rationale)
                        .font(.body)
                }
                
                // Key Metrics
                VStack(alignment: .leading, spacing: 16) {
                    Text("Key Metrics")
                        .font(.headline)
                    
                    MetricRow(title: "AI Score", value: String(format: "%.2f", opportunity.ai_score))
                    MetricRow(title: "Win Rate", value: String(format: "%.1f%%", opportunity.win_rate * 100))
                    MetricRow(title: "Max Profit", value: String(format: "$%.2f", opportunity.max_profit))
                    MetricRow(title: "Max Loss", value: String(format: "$%.2f", opportunity.risk_metrics.max_loss))
                    MetricRow(title: "DTE", value: "\(opportunity.dte)")
                }
                
                // Options Legs
                VStack(alignment: .leading, spacing: 8) {
                    Text("Strategy Legs")
                        .font(.headline)
                    
                    ForEach(opportunity.legs) { leg in
                        LegRowView(leg: leg)
                        Divider()
                    }
                }
            }
            .padding()
        }
        .navigationTitle(opportunity.symbol)
    }
}

struct MetricRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .fontWeight(.semibold)
        }
    }
}

struct LegRowView: View {
    let leg: OptionsLeg
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(leg.option_type)
                    .fontWeight(.bold)
                    .foregroundColor(leg.quantity > 0 ? .green : .red)
                Text(String(format: "%.2f Strike", leg.strike))
                Spacer()
                Text("Qty: \(leg.quantity)")
            }
            Text("Expires: \(leg.expiration)")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}
