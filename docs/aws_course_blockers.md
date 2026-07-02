# AWS Course Blockers - Course 1

Date: July 2026  
Course reviewed from screenshots: AWS / Amazon Bedrock AgentCore + CrewAI hands-on course

## Executive status

Status: BLOCKED for hands-on labs  
Impact: HIGH  
Reason: AWS account password has expired and requires reset before console/API access can continue.

Observed access error:

- AWS account: 648177073735
- User shown: Ameya_Dhake
- Error: Password has expired and requires reset. User must verify old password and set a new password.

## Main blocker

| Blocker | Impact | Status | Required action |
| --- | --- | --- | --- |
| AWS console access unavailable due to expired password | High - blocks all AWS hands-on work, deployments, invocations, and UI validation | Open | Account owner/admin must reset or rotate the password and confirm login works |

## Do not attempt until access is restored

These course items should not be started because they require active AWS access, IAM permissions, or AWS resource creation:

| Area | Course items affected | Why blocked |
| --- | --- | --- |
| Vacation Planner CrewAI app build | Pre-requisites, implementation, Streamlit UI, deployment | Requires environment setup and AWS-backed hands-on validation |
| AgentCore Runtime | Pre-requisites, decorator changes, Dockerfile, ECR, Runtime deployment | Requires AWS console/API, ECR, runtime creation, IAM permissions |
| Invocation flows | AgentCore invocation, Lambda invocation, REST API access, Streamlit deployment | Requires deployed runtime endpoint and credentials |
| AgentCore Observability | Introduction plus hands-on observability setup | Requires CloudWatch/AgentCore access and observability configuration |
| AgentCore Identity & Gateway | Basic concepts plus implementation and invocation parts 1-5 | Requires identity, gateway, IAM, and tool/API configuration |
| Agent-to-tool / package invocation | Travel package invocation via AgentCore Gateway | Requires working Gateway and runtime setup |
| AgentCore Memory | Basic concepts, adding memory, deployment to runtime | Requires AgentCore Memory resource creation and runtime integration |

## Items that can continue now

These are not blocked by AWS login and can be watched/reviewed while access is being fixed:

- Business use case / Financial Vacation Planner overview
- Basic concept videos for AgentCore Runtime, Gateway, Identity, Memory, and Observability
- CrewAI conceptual videos
- Outro or recap videos

## Relevance as of July 2026

Relevant course areas:

- Amazon Bedrock AgentCore Runtime
- Amazon Bedrock AgentCore Gateway
- Amazon Bedrock AgentCore Identity
- Amazon Bedrock AgentCore Memory
- Amazon Bedrock AgentCore Observability with CloudWatch / OpenTelemetry
- CrewAI agent framework concepts
- AWS Lambda, Amazon ECR, Docker, REST API, and Streamlit deployment patterns

Before restarting labs, verify:

- AWS login works for the correct course account.
- IAM permissions cover Bedrock AgentCore, Bedrock model access, Lambda, ECR, CloudWatch, IAM role/pass-role, and related networking/logging actions.
- The selected AWS Region supports the AgentCore features used in the course.
- Budget/cost controls are enabled before creating resources.

## Immediate ask for Nilesh / Ameya

1. Reset the expired AWS password for account 648177073735 / user Ameya_Dhake.
2. Confirm successful AWS console login.
3. Confirm required IAM permissions and Region availability.
4. Resume hands-on modules only after the above checks pass.
