package com.telenav.vde.compiler.util;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;
import com.esotericsoftware.kryo.serializers.CollectionSerializer;
import com.esotericsoftware.kryo.serializers.JavaSerializer;
import com.telenav.vde.compiler.feature.CityFeature;

public class SerializationHelper {
	public static void main(String[] args) {
		List<CityFeature> citylist = null;
		//
		citylist = KryoHelper.getSerializableObjectOriginal("D:\\test_temp\\vde20170914\\city_510000.out");
		writeSerializationListByKyro(citylist, CityFeature.class, "D:\\test_temp\\vde20170914\\city_510000_kryo.out");
	}

	public static <T> void writeSerializationListByKyro(List<T> tList, Class<T> clazz, String filename) {
		Date time0 = new Date();
		if (!tList.isEmpty()) {
			Kryo kryo = getKryo(clazz);
			
			Output output = null;
			try {
				output = new Output(new FileOutputStream(filename));
				kryo.writeObject(output, tList);

				output.flush();
				output.close();

				System.out.println(
						"write list to file by kryo finish.Time cost " + ((new Date()).getTime() - time0.getTime()));
			} catch (FileNotFoundException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}

		}

	}

	@SuppressWarnings("unchecked")
	public static <T> List<T> readSerializationListByKryo(String filename, Class<T> clazz) {
		Kryo kryo = getKryo(clazz);
		
		Input input;
		try {
			input = new Input(new FileInputStream(filename));

			List<T> citylist = kryo.readObject(input, ArrayList.class);

			input.close();

			return citylist;
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return null;
	}

	public static <T> Kryo getKryo(Class<T> clazz) {
		Kryo kryo = new Kryo();
		kryo.setReferences(false);
		kryo.setRegistrationRequired(true);

		CollectionSerializer serializer = new CollectionSerializer();
		serializer.setElementClass(clazz, new JavaSerializer());
		serializer.setElementsCanBeNull(false);

		kryo.register(clazz, new JavaSerializer());
		kryo.register(ArrayList.class, serializer);

		return kryo;
	}


	public static void writeSerializableObjectOriginal(List<CityFeature> citylist, String filename) {
		Date time0 = new Date();

		FileOutputStream fo;
		try {
			fo = new FileOutputStream(filename);
			ObjectOutputStream so = new ObjectOutputStream(fo);
			so.writeObject(citylist);
			so.flush();
			so.close();

			System.out.println("write list done");
			System.out.println("time cost " + ((new Date()).getTime() - time0.getTime()));
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

	public static List<CityFeature> getSerializableObjectOriginal(String filename) {
		Date time0 = new Date();

		FileInputStream fi;
		try {
			fi = new FileInputStream(filename);
			ObjectInputStream si = new ObjectInputStream(fi);

			List<CityFeature> citylist = (List<CityFeature>) si.readObject();

			fi.close();
			si.close();

			System.out.println("write done");
			System.out.println("time cost " + ((new Date()).getTime() - time0.getTime()));

			return citylist;
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {

			e.printStackTrace();
		} catch (ClassNotFoundException e) {
			e.printStackTrace();
		}
		return null;
	}
}
