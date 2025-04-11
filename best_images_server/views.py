from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageProcessingRequestSerializer, ImageProcessingResponseSerializer
import requests
import cv2
import numpy as np
from deepface import DeepFace

# Create your views here.

class BestImagesAPIView(APIView):
    """
    API endpoint that processes a list of S3 URLs and returns k best images.
    """
    def post(self, request):
        # Get data directly from request
        s3_urls = request.data['s3_urls']
        k = request.data['k']
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0'
            }
            happy_urls = []
            neutral_urls = []
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

            valid_emotions = ["happy", "neutral"]
            count =0;
            for image_url in s3_urls:
                try:
                    response = requests.get(image_url, headers=headers, timeout=10)
                    content_type = response.headers.get('Content-Type', '')

                    # Check 1 - Status code
                    if response.status_code != 200:
                        print(f"❌ Failed to fetch: {image_url} | Status: {response.status_code}")
                        continue

                    if response.status_code != 200:
                        print(f"❌ Failed to fetch: {image_url} | Status: {response.status_code}")
                        continue

                    # Check 2 - Acceptable content-type
                    if 'image' not in content_type and 'application/octet-stream' not in content_type:
                        print(f"❌ Invalid Content-Type: {content_type} for URL: {image_url}")
                        continue

                    # Check 3 - Buffer not empty
                    image_data = np.frombuffer(response.content, np.uint8)
                    if image_data.size == 0:
                        print(f"❌ Empty image data at: {image_url}")
                        continue

                    # Check 4 - Decoding image
                    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                    if img is None:
                        print(f"⚠️ Failed to decode image at: {image_url}")
                        continue

                    # Emotion Detection
                    result = DeepFace.analyze(img_path=img, actions=["emotion"], enforce_detection=False, detector_backend='opencv')
                    dominant_emotion = result[0]['dominant_emotion']
                    #print(f"{image_url} --> {dominant_emotion}")

                    # Collect based on emotion
                    if dominant_emotion == "happy":
                        happy_urls.append(image_url)
                    elif dominant_emotion == "neutral":
                        neutral_urls.append(image_url)
                    count+=1
                    if len(happy_urls) >= k:
                        return Response({
                            "success": "true",
                            "data": happy_urls
                        })
                    

                except Exception as e:
                    print(f"⚠️ Exception while processing {image_url}: {e}")

                # Pick Happy first then Neutral
            print("count", count);
            selected_urls = happy_urls[:k]

            if len(selected_urls) < k:
                remaining = k - len(selected_urls)
                selected_urls.extend(neutral_urls[:remaining])

                # If still nothing found
            if len(selected_urls) == 0:
                return Response({
                     "success": "false",
                     'data': [],
                     "error_type": "no_good_images_found",
                    "message": "No enough good images with happy or neutral emotion"
                })

            return Response({
                "success": "true",
                "data": selected_urls
            })


        except Exception as e:
            return Response(
                {  "success": "false",
                    "data": [],
                    "error_type": "error processing images",
                    "message": "Unable to process images"
                })
