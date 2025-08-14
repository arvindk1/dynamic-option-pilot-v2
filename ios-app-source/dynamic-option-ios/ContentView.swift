//
//  ContentView.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            NavigationView {
                DashboardView()
            }
            .tabItem {
                Label("Dashboard", systemImage: "house.fill")
            }
            
            NavigationView {
                OpportunitiesListView()
            }
            .tabItem {
                Label("Opportunities", systemImage: "list.bullet")
            }
        }
    }
}

// Renaming the original ContentView to be more specific
struct OpportunitiesListView: View {
    @StateObject private var viewModel = OpportunitiesViewModel()
    
    var body: some View {
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
                    if viewModel.isLoading {
                        ProgressView()
                    } else {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
        }
        .onAppear {
            viewModel.fetchOpportunities()
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

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
