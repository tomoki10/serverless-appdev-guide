import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

kinesis = boto3.client('kinesis')
cloudwatch = boto3.client('cloudwatch')

# Kinesis Data Streamの詳細は以下で参照
# 「Amazon Kinesis Data Streams の用語と概念」
# https://docs.aws.amazon.com/ja_jp/streams/latest/dev/key-concepts.html

def lambda_handler(event, context):

    # イベントデータからアラームに関するJSONを取得
    event_data = json.dumps(event,ensure_ascii=False,
        indent=4, sort_keys=True, separators=(',',': '))

    logger.info('Event' + event_data)
    # メッセージ部分のみ抽出
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Message: " + str(message))

    alarm_name = message['AlarmName']
    stream_name = message['Trigger']['Dimensions'][0]['value']

    if alarm_name == 'kinesis-mon':

        # 現在のオープンシャード数を取得
        # （シャード：ストリーム内の一意に識別されたデータレコードのシーケンス。
        # 　1シャード=1秒間1000レコード書き込み
        # 　など上限があるので大量にレコードを捌く場合はシャードを増やす必要がある。）
        stream_summary = kinesis.describe_stream_summary(
            StreamName = stream_name
        )
        current_open_shard_count = stream_summary['StreamDescriptionSummary']['OpenShardCount']

        # シャードを2倍に変更する
        target_shard_count=current_open_shard_count * 2
        response = kinesis.update_shard_count(
            StreamName=stream_name,
            TargetShardCount=target_shard_count,
            ScalingType='UNIFORM_SCALING'
        )

        # 現在のアラーム閾値をシャード数×1000 の 80 %に設定
        # (変更しない場合ずっとアラーム状態になるので変更している)
        new_threshold = target_shard_count*1000*0.8
        logger.info("Set a threshold value to " + str(new_threshold))
        response = cloudwatch.put_metric_alarm(
            AlarmName='kinesis-mon',
            MetricName='IncomingRecords',
            Namespace='AWS/Kinesis',
            Period=60,
            EvaluationPeriods=1,
            ComparisonOperator='GreaterThanThreshold',
            Threshold=new_threshold,
            Statistic='Sum'
        )