//
//  NetworkService.swift
//  dynamic-option-ios
//
//  Created by Gemini on 2025-08-14.
//

import Foundation

class NetworkService: ObservableObject {
    
    // Use the ngrok URL provided by the user
    private let baseURL = "https://worm-stunning-oriole.ngrok-free.app"
    
    enum NetworkError: Error {
        case invalidURL
        case requestFailed(Error)
        case invalidResponse
        case decodingError(Error)
    }
    
    // MARK: - Fetching Opportunities
    
    func fetchOpportunities() async throws -> [OpportunityCard] {
        guard let url = URL(string: "\(baseURL)/api/oppv2/opportunities") else {
            throw NetworkError.invalidURL
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                throw NetworkError.invalidResponse
            }
            
            do {
                let decodedResponse = try JSONDecoder().decode(OpportunitiesResponse.self, from: data)
                return decodedResponse.opportunities
            } catch {
                throw NetworkError.decodingError(error)
            }
        } catch {
            throw NetworkError.requestFailed(error)
        }
    }
    
    // MARK: - Triggering a Scan
    
    struct ScanTriggerBody: Codable {
        let universe: [String]
        let max_symbols: Int
    }
    
    struct ScanTriggerResponse: Codable {
        let scan_id: String
        let status: String
    }
    
    func triggerScan(universe: [String] = ["AAPL", "MSFT", "SPY", "QQQ", "TSLA"]) async throws -> String {
        guard let url = URL(string: "\(baseURL)/api/oppv2/scan/trigger") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ScanTriggerBody(universe: universe, max_symbols: universe.count)
        request.httpBody = try JSONEncoder().encode(body)
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                throw NetworkError.invalidResponse
            }
            
            do {
                let decodedResponse = try JSONDecoder().decode(ScanTriggerResponse.self, from: data)
                return decodedResponse.scan_id
            } catch {
                throw NetworkError.decodingError(error)
            }
        } catch {
            throw NetworkError.requestFailed(error)
        }
    }
    
    // MARK: - Fetching Market Movers
    
    func fetchMovers() async throws -> MoversResponse {
        guard let url = URL(string: "\(baseURL)/api/market/movers") else {
            throw NetworkError.invalidURL
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                throw NetworkError.invalidResponse
            }
            
            do {
                let decodedResponse = try JSONDecoder().decode(MoversResponse.self, from: data)
                return decodedResponse
            } catch {
                throw NetworkError.decodingError(error)
            }
        } catch {
            throw NetworkError.requestFailed(error)
        }
    }
}
