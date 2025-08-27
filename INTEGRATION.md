# Integration Guide: GoldWen Matching Service

This document provides guidance for integrating the GoldWen Matching Service with the main NestJS backend API.

## Service Architecture

```
┌─────────────────────┐    HTTP API calls    ┌──────────────────────┐
│                     │ ─────────────────→   │                      │
│   NestJS Main API   │                      │  Matching Service    │
│   (Port 3000)       │ ←───────────────     │  (Port 8000)         │
│                     │    JSON responses    │                      │
└─────────────────────┘                      └──────────────────────┘
           │                                            │
           │                                            │
           ▼                                            ▼
┌─────────────────────┐                      ┌──────────────────────┐
│  PostgreSQL         │◄─────────────────────┤  PostgreSQL          │
│  (Main Database)    │     Shared Database  │  (Matching Data)     │
└─────────────────────┘                      └──────────────────────┘
```

## Integration Points

### 1. User Onboarding Flow

When a user completes registration and personality questionnaire:

```typescript
// In your NestJS user service
async completeUserOnboarding(userId: number, userData: CreateUserDto, personalityResponses: PersonalityResponseDto[]) {
  // 1. Create user in main database
  const user = await this.userRepository.save(userData);
  
  // 2. Send user data to matching service
  await this.matchingService.createUser({
    id: user.id,
    email: user.email,
    first_name: user.firstName,
    age: user.age,
    gender: user.gender,
    location_city: user.city,
    location_latitude: user.latitude,
    location_longitude: user.longitude,
    is_premium: user.subscriptionType === 'premium'
  });
  
  // 3. Send personality responses
  await this.matchingService.submitPersonalityQuestionnaire(user.id, {
    responses: personalityResponses
  });
  
  return user;
}
```

### 2. Daily Selection Feature

Implement the daily ritual (12:00 PM selections):

```typescript
// Daily cron job or scheduled task
@Cron('0 12 * * *') // Daily at 12:00 PM
async sendDailySelections() {
  const activeUsers = await this.userRepository.findActiveUsers();
  
  for (const user of activeUsers) {
    try {
      // Get daily selection from matching service
      const selection = await this.matchingService.getDailySelection(user.id);
      
      if (selection.candidates.length > 0) {
        // Send push notification
        await this.notificationService.sendPushNotification(user.id, {
          title: 'Your GoldWen selection is ready! 🌟',
          body: `${selection.candidates.length} new profiles are waiting for you`,
          data: { type: 'daily_selection' }
        });
      }
    } catch (error) {
      console.error(`Failed to process daily selection for user ${user.id}:`, error);
    }
  }
}
```

### 3. User Choice Handling

When user makes a choice in the mobile app:

```typescript
// In your choices controller
@Post('users/:userId/choices')
async makeChoice(
  @Param('userId') userId: number,
  @Body() choiceDto: MakeChoiceDto
) {
  // Record choice in matching service
  const choice = await this.matchingService.recordUserChoice(userId, {
    chosen_user_id: choiceDto.chosenUserId
  });
  
  // If it's a match, send notifications
  if (choice.is_match) {
    await this.handleNewMatch(userId, choiceDto.chosenUserId);
  }
  
  return { success: true, isMatch: choice.is_match };
}

private async handleNewMatch(user1Id: number, user2Id: number) {
  // Create chat room
  const chatRoom = await this.chatService.createChatRoom(user1Id, user2Id);
  
  // Send match notifications
  const [user1, user2] = await Promise.all([
    this.userRepository.findOne(user1Id),
    this.userRepository.findOne(user2Id)
  ]);
  
  await Promise.all([
    this.notificationService.sendPushNotification(user1Id, {
      title: 'You have a new match! 💕',
      body: `You matched with ${user2.firstName}`,
      data: { type: 'new_match', chatRoomId: chatRoom.id }
    }),
    this.notificationService.sendPushNotification(user2Id, {
      title: 'You have a new match! 💕',
      body: `You matched with ${user1.firstName}`,
      data: { type: 'new_match', chatRoomId: chatRoom.id }
    })
  ]);
}
```

### 4. Subscription Management

Sync premium status changes:

```typescript
// When subscription status changes
async updateSubscription(userId: number, subscriptionType: 'free' | 'premium') {
  // Update in main database
  await this.userRepository.update(userId, { subscriptionType });
  
  // Sync with matching service
  await this.matchingService.updatePremiumStatus(userId, subscriptionType === 'premium');
}
```

## Matching Service Client

Create a service to handle all communication with the matching service:

```typescript
// matching-service.client.ts
@Injectable()
export class MatchingServiceClient {
  private readonly httpService: HttpService;
  private readonly baseUrl: string;
  
  constructor(httpService: HttpService, configService: ConfigService) {
    this.httpService = httpService;
    this.baseUrl = configService.get('MATCHING_SERVICE_URL', 'http://localhost:8000');
  }
  
  async createUser(userData: CreateUserForMatchingDto): Promise<void> {
    await this.httpService.post(`${this.baseUrl}/api/v1/users/`, userData).toPromise();
  }
  
  async submitPersonalityQuestionnaire(userId: number, questionnaire: PersonalityQuestionnaireDto): Promise<void> {
    await this.httpService.post(
      `${this.baseUrl}/api/v1/users/${userId}/personality`,
      questionnaire
    ).toPromise();
  }
  
  async getDailySelection(userId: number): Promise<DailySelectionResponse> {
    const response = await this.httpService.get(
      `${this.baseUrl}/api/v1/matching/daily-selection/${userId}`
    ).toPromise();
    return response.data;
  }
  
  async recordUserChoice(userId: number, choice: UserChoiceDto): Promise<UserChoiceResponse> {
    const response = await this.httpService.post(
      `${this.baseUrl}/api/v1/matching/user-choice/${userId}`,
      choice
    ).toPromise();
    return response.data;
  }
  
  async updatePremiumStatus(userId: number, isPremium: boolean): Promise<void> {
    await this.httpService.put(
      `${this.baseUrl}/api/v1/users/${userId}/premium`,
      { is_premium: isPremium }
    ).toPromise();
  }
  
  async calculateCompatibility(user1Id: number, user2Id: number): Promise<number> {
    const response = await this.httpService.post(
      `${this.baseUrl}/api/v1/matching/compatibility-score`,
      { user1_id: user1Id, user2_id: user2Id }
    ).toPromise();
    return response.data.compatibility_score;
  }
  
  async deleteUser(userId: number): Promise<void> {
    await this.httpService.delete(`${this.baseUrl}/api/v1/users/${userId}`).toPromise();
  }
}
```

## DTOs for Type Safety

```typescript
// dtos/matching.dto.ts
export class CreateUserForMatchingDto {
  id: number;
  email: string;
  first_name: string;
  age: number;
  gender: string;
  location_city: string;
  location_latitude?: number;
  location_longitude?: number;
  is_premium: boolean;
}

export class PersonalityResponseDto {
  question_id: number;
  response_value: number; // 1-5 scale
}

export class PersonalityQuestionnaireDto {
  responses: PersonalityResponseDto[];
}

export class DailySelectionCandidate {
  user_id: number;
  first_name: string;
  age: number;
  location_city: string;
  compatibility_score: number;
  rank_position: number;
}

export class DailySelectionResponse {
  user_id: number;
  selection_date: string;
  candidates: DailySelectionCandidate[];
  max_choices_allowed: number;
}

export class UserChoiceDto {
  chosen_user_id: number;
}

export class UserChoiceResponse {
  id: number;
  user_id: number;
  chosen_user_id: number;
  choice_date: string;
  is_match: boolean;
}
```

## Environment Configuration

```typescript
// In your NestJS config
export default () => ({
  matching: {
    serviceUrl: process.env.MATCHING_SERVICE_URL || 'http://localhost:8000',
    timeout: parseInt(process.env.MATCHING_SERVICE_TIMEOUT) || 5000,
  },
});
```

## Error Handling

```typescript
// Wrapper with error handling
async getDailySelectionSafely(userId: number): Promise<DailySelectionResponse | null> {
  try {
    return await this.matchingService.getDailySelection(userId);
  } catch (error) {
    console.error(`Failed to get daily selection for user ${userId}:`, error);
    
    // Fallback behavior - could show cached selections or empty state
    return {
      user_id: userId,
      selection_date: new Date().toISOString(),
      candidates: [],
      max_choices_allowed: 1
    };
  }
}
```

## Database Schema Synchronization

Ensure that the user IDs remain consistent between both services:

1. **User Creation**: Always create user in main database first, then send to matching service with the same ID
2. **User Updates**: Sync critical changes (premium status, location, etc.)
3. **User Deletion**: Delete from both services for GDPR compliance

## Performance Considerations

1. **Caching**: The matching service has built-in caching, but consider caching daily selections in Redis
2. **Async Processing**: Use queues for non-critical operations like sending selections to matching service
3. **Rate Limiting**: Implement rate limiting on choice endpoints to prevent abuse
4. **Circuit Breaker**: Use circuit breaker pattern for matching service calls

## Testing Integration

```typescript
// Mock the matching service for testing
const mockMatchingService = {
  getDailySelection: jest.fn().mockResolvedValue({
    user_id: 1,
    candidates: [
      {
        user_id: 2,
        first_name: 'Alice',
        age: 26,
        location_city: 'Paris',
        compatibility_score: 0.85,
        rank_position: 1
      }
    ],
    max_choices_allowed: 1
  })
};
```

This integration approach ensures a clean separation of concerns while maintaining data consistency and providing a seamless user experience.