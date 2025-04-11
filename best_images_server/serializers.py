from rest_framework import serializers

class ImageProcessingRequestSerializer(serializers.Serializer):
    s3_urls = serializers.ListField(
        child=serializers.URLField(),
        help_text="List of S3 URLs to process"
    )
    k = serializers.IntegerField(
        min_value=1,
        help_text="Number of best images to return"
    )

class ImageProcessingResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Status message of the API call")
    filtered_urls = serializers.ListField(
        child=serializers.URLField(),
        help_text="List of filtered S3 URLs"
    ) 