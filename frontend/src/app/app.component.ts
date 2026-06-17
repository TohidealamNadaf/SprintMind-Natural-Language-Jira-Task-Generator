import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SprintService, Ticket } from './sprint.service';
import { TicketCardComponent } from './ticket-card/ticket-card.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, TicketCardComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  brief: string = '';
  tickets: Ticket[] = [];
  loading: boolean = false;
  pushing: boolean = false;
  message: string = '';

  constructor(private sprintService: SprintService) {}

  generateTickets() {
    if (!this.brief.trim()) return;
    
    this.loading = true;
    this.message = '';
    this.tickets = [];
    
    this.sprintService.generateTickets(this.brief).subscribe({
      next: (res) => {
        this.tickets = res.tickets;
        this.loading = false;
      },
      error: (err) => {
        this.message = 'Error generating tickets: ' + err.message;
        this.loading = false;
      }
    });
  }

  pushToJira() {
    if (!this.tickets.length) return;
    
    this.pushing = true;
    this.message = '';
    
    this.sprintService.pushToJira(this.tickets).subscribe({
      next: (res) => {
        this.message = res.message;
        this.pushing = false;
      },
      error: (err) => {
        this.message = 'Error pushing to Jira: ' + err.message;
        this.pushing = false;
      }
    });
  }
}
