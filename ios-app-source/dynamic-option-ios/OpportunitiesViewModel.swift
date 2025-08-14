//
//  OpportunitiesViewModel.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import Foundation
import Combine

// Custom Error type to be Identifiable for SwiftUI Alerts
struct AppError: Identifiable {
    let id = UUID()
    let underlyingError: Error
    
    var localizedDescription: String {
        return underlyingError.localizedDescription
    }
}

@MainActor
class OpportunitiesViewModel: ObservableObject {
    
    @Published var opportunities: [OpportunityCard] = []
    @Published var isLoading: Bool = false
    @Published var error: AppError?
    
    private let networkService = NetworkService()
    
    func fetchOpportunities() {
        isLoading = true
        Task {
            do {
                let fetchedOpportunities = try await networkService.fetchOpportunities()
                self.opportunities = fetchedOpportunities
            } catch {
                self.error = AppError(underlyingError: error)
            }
            isLoading = false
        }
    }
    
    func triggerScan() {
        isLoading = true
        Task {
            do {
                let scanId = try await networkService.triggerScan()
                print("Scan triggered with ID: \(scanId)")
                // Wait a few seconds for the scan to process on the backend
                try await Task.sleep(nanoseconds: 5_000_000_000) // 5 seconds
                fetchOpportunities()
            } catch {
                self.error = AppError(underlyingError: error)
                isLoading = false
            }
        }
    }
}
