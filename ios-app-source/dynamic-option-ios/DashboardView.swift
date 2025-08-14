//
//  DashboardView.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import SwiftUI

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                if let movers = viewModel.movers {
                    TopMoversView(movers: movers)
                }
                
                // Other widgets will be added here
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("Dashboard")
        .onAppear {
            viewModel.loadDashboardData()
        }
        .overlay {
            if viewModel.isLoading {
                ProgressView("Loading Dashboard...")
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

struct DashboardView_Previews: PreviewProvider {
    static var previews: some View {
        DashboardView()
    }
}
