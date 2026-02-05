calendar = """CREATE TABLE public.calendar (
	service_id text NULL,
	start_date text NULL,
	end_date text NULL,
	monday text NULL,
	tuesday text NULL,
	wednesday text NULL,
	thursday text NULL,
	friday text NULL,
	saturday text NULL,
	sunday text NULL
);"""

calendar_date = """CREATE TABLE public.calendar_dates (
	service_id text NULL,
	datet text NULL,
	date text NULL,
	exception_type text NULL
);"""

fare_attributes ="""CREATE TABLE public.fare_attributes (
	fare_id text NULL,
	price text NULL,
	currency_type text NULL,
	payment_method text NULL,
	transfers text NULL,
	transfer_duration text NULL
);"""

farerules = """CREATE TABLE public.farerules (
	fare_id text NULL,
	route_id text NULL,
	origin_id text NULL,
	destination_id text NULL,
	contains_id text NULL
);"""

route = """CREATE TABLE public.route (
	route_type text NULL,
	route_id text NULL,
	route_short_name text NULL,
	route_long_name text NULL,
	agency_id text NULL,
	route_desc text NULL,
	route_url text NULL,
	route_color text NULL,
	route_text_color text NULL
);"""

shape = """CREATE TABLE public.shape (
	shape_id text NULL,
	shape_pt_lat text NULL,
	shape_pt_lon float4 NULL,
	shape_pt_sequence int4 NULL,
	shape_dist_traveled text NULL
);"""

stops = """CREATE TABLE public.stops (
	stop_code text NULL,
 	stop_name text NULL,
	stop_id text NULL,
	stop_lat float4 NULL,
	stop_lon float4 NULL,
	parent_station text NULL,
	location_type text NULL,
	zone_id text NULL,
 	wheelchair_boarding TEXT NULL
);"""

stopstime = """CREATE TABLE public.stopstime (
	trip_id text NULL,
	arrival_time text NULL,
	departure_time text NULL,
	stop_id text NULL,
	stop_sequence int4 NULL,
	stop_headsign text NULL,
	pickup_type text NULL,
	drop_off_type text NULL,
	shape_dist_traveled text NULL,
	timepoint text NULL
);"""

trip = """CREATE TABLE public.trip (
	trip_id text NULL,
	route_id text NULL,
	trip_headsign text NULL,
	service_id text NULL,
	shape_id text NULL,
	block_id text NULL,
	wheelchair_accessible text NULL,
	bikes_allowed text NULL,
	direction_id text NULL
);"""




table_names = ["calendar","calendar_dates","farerules", "fare_attributes", "route", "shape", "stops","stopstime", "trip"]
tables = [calendar,calendar_date, fare_attributes, farerules, route, shape, stops,stopstime, trip]

stoptimeindex="create index IDX_STOP_TRIP on stopstime (trip_id,stop_id)"
stop_timesindex = "create index idx_stop_stoptimes on stopstime(stop_id)"

indexes = [stoptimeindex,stop_timesindex]
