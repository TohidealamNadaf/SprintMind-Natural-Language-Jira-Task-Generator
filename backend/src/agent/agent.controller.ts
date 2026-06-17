import { Controller, Post, Body } from '@nestjs/common';
import { AgentService } from './agent.service';
import { GenerateRequestDto, PushRequestDto } from './generate.dto';

@Controller('api')
export class AgentController {
  constructor(private readonly agentService: AgentService) {}

  @Post('generate')
  async generateTickets(@Body() request: GenerateRequestDto) {
    return this.agentService.generateTickets(request.brief);
  }

  @Post('push')
  async pushTickets(@Body() request: PushRequestDto) {
    return this.agentService.pushTickets(request.tickets);
  }
}
