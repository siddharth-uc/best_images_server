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
def is_blurry(img, threshold=100.0):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold


class BestImagesAPIView(APIView):
    """
    API endpoint that processes a list of S3 URLs and returns k best images.
    """
    def post(self, request):
        # Get data directly from request
        s3_urls = request.data['s3_urls']
        k = request.data['k']
        try: 
            headers = {'User-Agent': 'Mozilla/5.0'}
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

            happy_sharp, happy_blur, neutral_sharp, neutral_blur = [], [], [], []

            for image_url in s3_urls:
                try:
                    response = requests.get(image_url, headers=headers, timeout=10)
                    content_type = response.headers.get('Content-Type', '')

                    if response.status_code != 200 or ('image' not in content_type and 'application/octet-stream' not in content_type):
                        continue

                    image_data = np.frombuffer(response.content, np.uint8)
                    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

                    if img is None or image_data.size == 0:
                        continue

                    result = DeepFace.analyze(img_path=img, actions=["emotion"], enforce_detection=False, detector_backend='opencv')
                    dominant_emotion = result[0]['dominant_emotion']

                    blurry = is_blurry(img)

                    # Priority-wise storing
                    if dominant_emotion == "happy":
                        if not blurry:
                            happy_sharp.append(image_url)
                            if len(happy_sharp) == k:
                                return Response({"success": "true", "data": happy_sharp})
                        else:
                            happy_blur.append(image_url)
                    elif dominant_emotion == "neutral":
                        if not blurry:
                            neutral_sharp.append(image_url)
                        else:
                            neutral_blur.append(image_url)

                except Exception as e:
                    print(f"Error processing {image_url}: {e}")

            # Final selection based on priority buckets
            selected_urls = []

            # Priority 1: Happy + Sharp
            for url in happy_sharp:
                    if len(selected_urls) < k:
                        selected_urls.append(url)
                    else:
                        break

                # Priority 2: Happy + Blur
            for url in happy_blur:
                    if len(selected_urls) < k:
                        selected_urls.append(url)
                    else:
                        break

                # Priority 3: Neutral + Sharp
            for url in neutral_sharp:
                    if len(selected_urls) < k:
                        selected_urls.append(url)
                    else:
                        break

                # Priority 4: Neutral + Blur
            for url in neutral_blur:
                    if len(selected_urls) < k:
                        selected_urls.append(url)
                    else:
                        break


            if not selected_urls:
                    return Response({
                        "success": "false",
                        "data": [],
                        "error_type": "no_good_images_found",
                        "message": "No good images found with required conditions"
                    })

            return Response({"success": "true", "data": selected_urls})


        except Exception as e:
            return Response(
                {  "success": "false",
                    "data": [],
                    "error_type": "error processing images",
                    "message": "Unable to process images"
                })
