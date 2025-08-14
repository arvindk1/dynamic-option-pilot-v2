//
//  DashboardViewModel.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import Foundation
import Combine

@MainActor
class DashboardViewModel: ObservableObject {
    
    @Published var movers: MoversResponse?
    @Published var isLoading: Bool = false
    @Published var error: AppError?
    
    private let networkService = NetworkService()
    
    func loadDashboardData() {
        isLoading = true
        Task {
            do {
                self.movers = try await networkService.fetchMovers()
            } catch {
                self.error = AppError(underlyingError: error)
            }
            isLoading = false
        }
    }
}
