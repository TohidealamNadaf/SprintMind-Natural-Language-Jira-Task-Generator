import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Ticket {
  type: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  story_points: number;
  parent?: string;
}

export interface GenerateResponse {
  tickets: Ticket[];
}

export interface PushResponse {
  created: any[];
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class SprintService {
  private apiUrl = 'http://localhost:3000/api';

  constructor(private http: HttpClient) { }

  generateTickets(brief: string): Observable<GenerateResponse> {
    return this.http.post<GenerateResponse>(`${this.apiUrl}/generate`, { brief });
  }

  pushToJira(tickets: Ticket[]): Observable<PushResponse> {
    return this.http.post<PushResponse>(`${this.apiUrl}/push`, { tickets });
  }
}
