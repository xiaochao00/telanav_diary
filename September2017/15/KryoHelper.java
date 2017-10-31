package com.telenav.vde.compiler.util;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;
import com.esotericsoftware.kryo.serializers.CollectionSerializer;
import com.esotericsoftware.kryo.serializers.JavaSerializer;
import com.telenav.vde.compiler.feature.CityFeature;

public class KryoHelper {
	public static void main(String[] args) throws IOException {
		//
		List<CityFeature> citylist = new ArrayList<CityFeature>();
		//
		citylist = KryoHelper.getSerializableObjectOriginal("D:\\test_temp\\vde20170914\\city_510000.out");
		setSerializationObjectKryo(citylist, CityFeature.class,
				"D:\\test_temp\\vde20170914\\city_510000_kryo.out");
		//
		citylist = getSerializationObject("D:\\test_temp\\vde20170914\\city_510000_kryo.out", CityFeature.class);
		KryoHelper.setSerializableObjectOriginal(citylist, "D:\\\\test_temp\\\\vde20170914\\\\city_510000_orignal.out");
		//
	}

	/**
	 * Serialization object to file
	 * 
	 * @param <T>
	 * 
	 * @param <T>
	 * 
	 * @param citylist
	 * @param filename
	 */
	public static <T extends Serializable> void setSerializationObjectKryo(List<T> citylist, Class<T> clazz,
			String filename) {
		Date time0 = new Date();

		try {
			Kryo kryo = new Kryo();
			kryo.setReferences(false);
			kryo.setRegistrationRequired(true);
			kryo.register(CityFeature.class);

			CollectionSerializer serializer = new CollectionSerializer();
			serializer.setElementClass(clazz, new JavaSerializer());
			serializer.setElementsCanBeNull(false);

			kryo.register(clazz, new JavaSerializer());
			kryo.register(ArrayList.class, serializer);

			Output output = new Output(new FileOutputStream(filename));
			kryo.writeObject(output, citylist);

			System.out.println("write done " + filename);
			System.out.println("time cost " + ((new Date()).getTime() - time0.getTime()));

			output.flush();
			output.close();

		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(-1);
		}
	}

	/**
	 * get the serialization object
	 * 
	 * @param <T>
	 * 
	 * @param cla
	 * @return
	 */
	@SuppressWarnings("unchecked")
	public static <T extends Serializable> List<T> getSerializationObject(String filename, Class<T> clazz) {
		Date time0 = new Date();

		Kryo kryo = new Kryo();
		kryo.setReferences(false);
		kryo.setRegistrationRequired(true);

		CollectionSerializer serializer = new CollectionSerializer();
		serializer.setElementClass(clazz, new JavaSerializer());
		serializer.setElementsCanBeNull(false);

		kryo.register(clazz, new JavaSerializer());
		kryo.register(ArrayList.class, serializer);

		Input input;
		try {
			input = new Input(new FileInputStream(filename));

			List<T> citylist = kryo.readObject(input, ArrayList.class);

			input.close();

			System.out.println("write done");
			System.out.println("time cost " + ((new Date()).getTime() - time0.getTime()));
			return citylist;
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
		return null;
	}

	public static void setSerializableObjectOriginal(List<CityFeature> citylist, String filename) throws IOException {
		Date time0 = new Date();

		FileOutputStream fo = new FileOutputStream(filename);
		ObjectOutputStream so = new ObjectOutputStream(fo);
		so.writeObject(citylist);
		so.flush();
		so.close();

		System.out.println("write done");
		System.out.println("time cost " + ((new Date()).getTime() - time0.getTime()));
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

			System.out.println("read list");
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
