import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { AgentController } from './agent.controller';
import { AgentService } from './agent.service';

@Module({
  imports: [HttpModule],
  controllers: [AgentController],
  providers: [AgentService],
})
export class AgentModule {}
