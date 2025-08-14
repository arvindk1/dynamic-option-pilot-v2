//
//  ContentView.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = OpportunitiesViewModel()
    
    var body: some View {
        NavigationView {
            List(viewModel.opportunities) { opportunity in
                NavigationLink(destination: OpportunityDetailView(opportunity: opportunity)) {
                    OpportunityRowView(opportunity: opportunity)
                }
            }
            .navigationTitle("Trading Opportunities")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        viewModel.triggerScan()
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .onAppear {
                viewModel.fetchOpportunities()
            }
            .overlay {
                if viewModel.isLoading {
                    ProgressView("Scanning...")
                }
            }
            .alert(item: $viewModel.error) { error in
                Alert(
                    title: Text("Error"),
                    message: Text(error.localizedDescription),
                    dismissButton: .default(Text("OK"))
                )
            }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
