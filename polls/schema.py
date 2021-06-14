import graphene
from graphene_django import DjangoObjectType
from django.db.models import Q

from users.schema import UserType
from polls.models import Poll, Vote

from .models import Poll


class PollType(DjangoObjectType):
    class Meta:
        model = Poll

class VoteType(DjangoObjectType):
    class Meta:
        model = Vote

class Query(graphene.ObjectType):
    polls = graphene.List(PollType, search=graphene.String())
    votes = graphene.List(VoteType, search=graphene.String())

    def resolve_polls(self, info, search=None, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged to add a poll.')

        if search:
            filter = (
                Q(url__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
            return Poll.objects.filter(filter)
        return Poll.objects.all()

    def resolve_votes(self, info, **kwargs):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged view votes.')
        
        filter = (
            (
                Q(user__id=user.id) & Q(poll__is_open=True)
            ) |
            Q(poll__is_open=False)
        )
        return Vote.objects.filter(filter)

class CreatePoll(graphene.Mutation):
    id = graphene.Int()
    url = graphene.String()
    name = graphene.String()
    description = graphene.String()
    posted_by = graphene.Field(UserType)
    is_open = graphene.Boolean()

    class Arguments:
        url = graphene.String()
        name = graphene.String()
        description = graphene.String()

    def mutate(self, info, url, name, description):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged to add a poll.')

        poll = Poll(url=url, name=name, description=description, posted_by=user,)
        poll.save()

        return CreatePoll(
            id=poll.id,
            url=poll.url,
            name=poll.name,
            description=poll.description,
            posted_by=poll.posted_by,
        )

class ClosePoll(graphene.Mutation):
    is_open = graphene.Boolean()
    result = graphene.Int()

    class Arguments:
        poll_id = graphene.Int()

    def mutate(self, info, poll_id):
        print("ClosePoll called: poll_id: ", poll_id)
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged to close a poll.')

        if Poll.objects.filter(id=poll_id).count() == 0:
            raise Exception('Poll doesn\'t exist.')

        Poll.objects.filter(id=poll_id).update(is_open=False)

        vote_counts = {}
        votes = Vote.objects.filter(poll_id=poll_id)
        for vote in votes:
            if not vote.weight in vote_counts:
                vote_counts[vote.weight] = 0

            vote_counts[vote.weight]+=1

        result = 0
        for weight, count in vote_counts.items():
            if count>=result:
                result = weight
        return ClosePoll(
            is_open=False, result=result
        )

class CreateVote(graphene.Mutation):
    user = graphene.Field(UserType)
    poll = graphene.Field(PollType)

    class Arguments:
        poll_id = graphene.Int()
        weight = graphene.Int()

    def mutate(self, info, poll_id, weight):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged to vote.')

        if weight not in [1, 2, 3, 5, 8, 13, 21]:
            raise Exception('Invalid weight.')

        poll = Poll.objects.filter(id=poll_id).first()
        if not poll:
            raise Exception('Invalid Poll.')

        if poll.is_open==False:
            raise Exception('Poll is closed.')

        if Vote.objects.filter(user=user).filter(poll=poll_id).count():
            Vote.objects.filter(user=user).filter(poll=poll_id).delete()

        Vote.objects.create(
            user=user,
            poll=poll,
            weight=weight,
        )

        return CreateVote(user=user, poll=poll)

class Mutation(graphene.ObjectType):
    create_poll = CreatePoll.Field()
    close_poll = ClosePoll.Field()
    create_vote = CreateVote.Field()
