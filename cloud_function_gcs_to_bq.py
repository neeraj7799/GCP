def big_query_import(data,context,dataset_id='sample_dataset_id',table_id='sample_table',verbose=True):
    from google.cloud import bigquery
    from datetime import datetime, timezone
	# The 'python-dateutil' package must be included in requirements.txt.
    from dateutil import parser
    timestamp = context.timestamp
    event_time = parser.parse(timestamp)
    event_age = (datetime.now(timezone.utc) - event_time).total_seconds()
    event_age_ms = event_age * 1000
    max_age_ms = 10000
    if event_age_ms > max_age_ms:
        print('Dropped {} (age {}ms)'.format(context.event_id, event_age_ms))
        return 'Timeout'
    if verbose:
        input_bucket_name = data['bucket']
        source_file = data['name']
        uri = 'gs://{}/{}'.format(input_bucket_name, source_file)
        print('Event ID: {}'.format(context.event_id))
        print('Event type: {}'.format(context.event_type))
        print('Bucket: {}'.format(data['bucket']))
        print('File: {}'.format(data['name']))
        print('Metageneration: {}'.format(data['metageneration']))
        print('Created: {}'.format(data['timeCreated']))
        print('Updated: {}'.format(data['updated']))
        if str(source_file).lower().endswith('.csv'):
            client = bigquery.Client()
            dataset_ref = client.dataset(dataset_id)
            job_config = bigquery.LoadJobConfig()
            job_config.autodetect = True
            job_config.schema_update_options = [
	            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
	        ]
            job_config.source_format = bigquery.SourceFormat.CSV
            load_job = client.load_table_from_uri(
	            uri,
	            dataset_ref.table(table_id),
	            job_config=job_config)
            print('Starting job {}'.format(load_job.job_id))
            load_job.result()
            print('Job Finished')
        destination_table = client.get_table(dataset_ref.table(table_id))
        print('Loaded {} rows.'.format(destination_table.num_rows))

        print('File imported successfully.')
    else:
    	print('File import failed')



	
