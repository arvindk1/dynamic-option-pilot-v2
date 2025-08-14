//
//  TopMoversView.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import SwiftUI

struct TopMoversView: View {
    let movers: MoversResponse
    @State private var selectedTab: MoverType = .gainers
    
    enum MoverType: String, CaseIterable {
        case gainers = "Top Gainers"
        case losers = "Top Losers"
        case active = "Most Active"
    }
    
    var body: some View {
        VStack(alignment: .leading) {
            Text("Top Market Movers")
                .font(.headline)
                .padding(.horizontal)
            
            Picker("Mover Type", selection: $selectedTab) {
                ForEach(MoverType.allCases, id: .self) { type in
                    Text(type.rawValue).tag(type)
                }
            }
            .pickerStyle(SegmentedPickerStyle())
            .padding(.horizontal)
            
            VStack(spacing: 12) {
                ForEach(stocksForSelectedTab()) { stock in
                    MoverRow(stock: stock)
                }
            }
            .padding()
            .background(Color(.secondarySystemBackground))
            .cornerRadius(12)
        }
    }
    
    private func stocksForSelectedTab() -> [MoverStock] {
        switch selectedTab {
        case .gainers:
            return movers.gainers
        case .losers:
            return movers.losers
        case .active:
            return movers.most_active
        }
    }
}

struct MoverRow: View {
    let stock: MoverStock
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(stock.symbol)
                    .fontWeight(.bold)
                Text(stock.name)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }
            
            Spacer()
            
            Text(String(format: "$%.2f", stock.price))
                .fontWeight(.semibold)
            
            Text(String(format: "%.2f%%", stock.change_percent))
                .foregroundColor(stock.change_percent >= 0 ? .green : .red)
                .frame(width: 70, alignment: .trailing)
        }
    }
}
