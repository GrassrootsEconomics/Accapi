""" SCHEMA SCRIPT
This script is responsible for handling charts based on a number of categories, i.e. trade volume by gender.
it makes use of functions defined in the functions script (located in parent folder > graphqlAPI)
where possible repetitive steps have been transformed into a function for simplicity.
"""

from .types import *
from .. functions import *

cic_users = models.CicUsers
reporting_table = models.CicReportingTable

class Query(graphene.ObjectType):

	categorySummary = graphene.List(category_summary,
		from_date = graphene.String(required=True), 
		to_date = graphene.String(required=True),
		token_name= graphene.List(graphene.String,required=True),
		spend_type =graphene.List(graphene.String,required=True),
		gender =graphene.List(graphene.String,required=True), 
		tx_type =graphene.List(graphene.String,required=True),
		request = graphene.String(required=True))


	def resolve_categorySummary(self, info, **kwargs):

		if CACHE_ENABLED:
			cache_key = kwargs
			cache_key.update({"Query":"categorySummary"})
			response = cache.get(cache_key)

			if response is not None:
				return(response)

		from_date, to_date, token_name, spend_type, gender, tx_type, request = kwargs['from_date'], kwargs['to_date'], kwargs['token_name'], kwargs['spend_type'], kwargs['gender'], kwargs['tx_type'], kwargs['request']
		start_period_first, start_period_last, end_period_first, end_period_last, _= create_date_range(from_date, to_date)
		gender_filter, spend_filter, token_name_filter, tx_type_filter = create_filter_items(gender, spend_type, token_name, tx_type)
		
		reporting_data = reporting_table.objects.all()		
		summary_data = reporting_data\
		.filter(
			timestamp__gte = start_period_first,
			timestamp__lt = end_period_last, 
			tokenname__in = token_name_filter,
			t_business_type__in = spend_filter,
			s_gender__in = gender_filter,
			transfer_subtype__in = tx_type_filter)

		request = request.lower()

		if request == 'tradevolumes-category-spendtype':
			data =summary_data.annotate(label = F('t_business_type')).values("label").annotate(value=Sum("weight"))
			
			result = []
			for stype in spend_filter:
				temp_dict = {}
				x = [{'label':e['label'], 'value':e['value']} for e in data if e['label'] == stype]
				if len(x) > 0:
					result.append(x[0])
				else:
					result.append({'label':stype, 'value':0})

			response = [category_summary(label=i['label'], value =i['value']) for i in result]

		if request == 'tradevolumes-category-gender':
			data =summary_data.annotate(label = F('s_gender')).values("label").annotate(value=Sum("weight"))
			response = [category_summary(label=i['label'], value =i['value']) for i in data]

		if CACHE_ENABLED:
			cache.set(cache_key,response, CACHE_TTL)

		return(response)

	summaryDataTopTraders = graphene.List(time_summary,
		from_date = graphene.String(required=True), 
		to_date = graphene.String(required=True),
		token_name = graphene.List(graphene.String,required=True),
		business_type = graphene.List(graphene.String,required=True), # this is spend_type i.e. the targets business type
		gender = graphene.List(graphene.String,required=True))

	def resolve_summaryDataTopTraders(self, info, **kwargs):

		if CACHE_ENABLED:
			cache_key = kwargs
			cache_key.update({"Query":"summaryDataTopTraders"})
			response = cache.get(cache_key)

			if response is not None:
				return(response)

		from_date, to_date, token_name, spend_type, gender = kwargs['from_date'], kwargs['to_date'], kwargs['token_name'], kwargs['business_type'], kwargs['gender']
		start_period_first, start_period_last, end_period_first, end_period_last, _ = create_date_range(from_date, to_date)
		gender_filter, spend_filter, token_name_filter, _ = create_filter_items(gender, spend_type, token_name, [])

		reporting_data = reporting_table.objects.all()
		summary_data = reporting_data.annotate(_month=TruncMonth('timestamp'))\
		.filter(
			timestamp__gte = start_period_first,
			timestamp__lt = end_period_last, 
			tokenname__in = token_name_filter, 
			t_business_type__in = spend_filter, 
			s_gender__in = gender_filter,
			transfer_subtype = 'STANDARD'
			).order_by("_month")

		top_ten_traders = summary_data.values('source', 's_gender', 's_business_type')\
		.annotate(volume = Coalesce(Sum("weight"),0), count = Coalesce(Count("id"),0),).order_by('-volume')[:10]

		response = [time_summary(value=top_ten_traders)]

		if CACHE_ENABLED:
			cache.set(cache_key,response, CACHE_TTL)
		
		return(response)
