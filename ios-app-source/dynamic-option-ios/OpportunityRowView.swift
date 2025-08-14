//
//  OpportunityRowView.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import SwiftUI

struct OpportunityRowView: View {
    let opportunity: OpportunityCard
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(opportunity.symbol)
                    .font(.headline)
                    .fontWeight(.bold)
                Text(opportunity.strategy_type.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text(String(format: "%.2f", opportunity.ai_score))
                    .font(.headline)
                    .foregroundColor(opportunity.ai_score > 75 ? .green : .orange)
                Text("AI Score")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 8)
    }
}
