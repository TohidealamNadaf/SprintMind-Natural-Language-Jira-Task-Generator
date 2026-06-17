import { Injectable, HttpException, HttpStatus } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';

@Injectable()
export class AgentService {
  private readonly agentUrl = 'http://localhost:8000';

  constructor(private readonly httpService: HttpService) {}

  async generateTickets(brief: string) {
    try {
      const response = await firstValueFrom(
        this.httpService.post(`${this.agentUrl}/generate`, { brief })
      );
      return response.data;
    } catch (error: any) {
      throw new HttpException(
        error.response?.data || 'Error connecting to Python agent',
        error.response?.status || HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  async pushTickets(tickets: any[]) {
    try {
      const response = await firstValueFrom(
        this.httpService.post(`${this.agentUrl}/push`, { tickets })
      );
      return response.data;
    } catch (error: any) {
      throw new HttpException(
        error.response?.data || 'Error pushing tickets to Jira via agent',
        error.response?.status || HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }
}
